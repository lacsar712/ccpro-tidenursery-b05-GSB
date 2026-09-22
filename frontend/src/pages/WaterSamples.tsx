import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Hatchery, Pond, WaterSample } from '../types'

function toLocalInput(iso: string) {
  const d = new Date(iso)
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

function nowLocal() {
  return toLocalInput(new Date().toISOString())
}

const empty = {
  pondId: 0,
  sampledAt: nowLocal(),
  tempC: 26,
  salinityPpt: 28,
  doMgL: 6.5,
  ph: 8.0,
  notes: '',
  sourceConfirmation: '',
}

export default function WaterSamples() {
  const [ponds, setPonds] = useState<Pond[]>([])
  const [hatcheries, setHatcheries] = useState<Hatchery[]>([])
  const [rows, setRows] = useState<WaterSample[]>([])
  const [form, setForm] = useState(empty)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')

  async function load() {
    const [ps, hs, ws] = await Promise.all([
      api<Pond[]>('/api/ponds'),
      api<Hatchery[]>('/api/hatcheries'),
      api<WaterSample[]>('/api/water-samples'),
    ])
    setPonds(ps)
    setHatcheries(hs)
    setRows(ws)
    if (!form.pondId && ps[0]) {
      setForm((f) => ({ ...f, pondId: ps[0].id }))
    }
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const hatcheryByPond = (pondId: number): Hatchery | undefined => {
    const pond = ponds.find((p) => p.id === pondId)
    return hatcheries.find((h) => h.id === pond?.hatcheryId)
  }

  const activeHatchery = hatcheryByPond(form.pondId)
  const confirmationRequired = !!activeHatchery?.sourceConfirmationOpen
  // 切换事务会把场海水源字段更新为新水源摘要，二者一致，可直接作为预填值。
  const expectedSource = activeHatchery?.seawaterSource ?? ''

  function selectPond(pondId: number) {
    const h = hatcheryByPond(pondId)
    setForm((f) => ({
      ...f,
      pondId,
      sourceConfirmation: h?.sourceConfirmationOpen ? h.seawaterSource : '',
    }))
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    const payload = {
      ...form,
      sampledAt: new Date(form.sampledAt).toISOString(),
      ...(confirmationRequired
        ? { sourceConfirmation: form.sourceConfirmation }
        : {}),
    }
    try {
      if (editingId === null) {
        await api('/api/water-samples', { method: 'POST', body: JSON.stringify(payload) })
      } else {
        await api(`/api/water-samples/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        })
      }
      resetForm()
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    }
  }

  function resetForm() {
    setEditingId(null)
    setForm((f) => ({ ...empty, pondId: f.pondId, sampledAt: nowLocal() }))
  }

  function startEdit(r: WaterSample) {
    setError('')
    setEditingId(r.id)
    const h = hatcheryByPond(r.pondId)
    setForm({
      pondId: r.pondId,
      sampledAt: toLocalInput(r.sampledAt),
      tempC: r.tempC,
      salinityPpt: r.salinityPpt,
      doMgL: r.doMgL,
      ph: r.ph,
      notes: r.notes ?? '',
      sourceConfirmation: h?.sourceConfirmationOpen ? h.seawaterSource : '',
    })
  }

  async function remove(id: number) {
    if (!confirm('确认删除该水质样？')) return
    try {
      await api(`/api/water-samples/${id}`, { method: 'DELETE' })
      if (editingId === id) resetForm()
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  const pondLabel = (id: number) => {
    const p = ponds.find((x) => x.id === id)
    return p ? `${p.pondCode} (${p.species})` : `#${id}`
  }

  return (
    <div>
      <header className="page-header">
        <h1>水质采样</h1>
        <p className="muted">
          校验：溶解氧 doMgL &gt; 0，pH ∈ [6, 9]；塘口所属场海水源切换 24 小时内须带水源确认，否则 409
        </p>
      </header>
      {error && <div className="error">{error}</div>}

      <form className="panel form-grid" onSubmit={onSubmit}>
        <label>
          塘口
          <select
            value={form.pondId}
            onChange={(e) => selectPond(Number(e.target.value))}
            required
          >
            {ponds.map((p) => (
              <option key={p.id} value={p.id}>
                {p.pondCode} · {p.species}
              </option>
            ))}
          </select>
        </label>
        <label>
          采样时间
          <input
            type="datetime-local"
            value={form.sampledAt}
            onChange={(e) => setForm({ ...form, sampledAt: e.target.value })}
            required
          />
        </label>
        <label>
          水温 °C
          <input
            type="number"
            step="0.1"
            value={form.tempC}
            onChange={(e) => setForm({ ...form, tempC: Number(e.target.value) })}
            required
          />
        </label>
        <label>
          盐度 ppt
          <input
            type="number"
            step="0.1"
            value={form.salinityPpt}
            onChange={(e) => setForm({ ...form, salinityPpt: Number(e.target.value) })}
            required
          />
        </label>
        <label>
          溶解氧 mg/L
          <input
            type="number"
            step="0.1"
            value={form.doMgL}
            onChange={(e) => setForm({ ...form, doMgL: Number(e.target.value) })}
            required
          />
        </label>
        <label>
          pH
          <input
            type="number"
            step="0.1"
            value={form.ph}
            onChange={(e) => setForm({ ...form, ph: Number(e.target.value) })}
            required
          />
        </label>
        <label className="span-2">
          备注
          <input
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
          />
        </label>

        {confirmationRequired && (
          <label className="span-2 confirm-field">
            水源确认（该场海水源切换未满 24 小时，须与新水源摘要一致：{expectedSource}）
            <input
              value={form.sourceConfirmation}
              onChange={(e) =>
                setForm({ ...form, sourceConfirmation: e.target.value })
              }
              placeholder={`请输入新水源摘要，如：${expectedSource}`}
              required
            />
          </label>
        )}

        <div className="form-actions">
          <button type="submit" className="btn primary">
            {editingId === null ? '登记水质样' : '保存修改'}
          </button>
          {editingId !== null && (
            <button type="button" className="btn ghost" onClick={resetForm}>
              取消编辑
            </button>
          )}
        </div>
      </form>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>塘口</th>
              <th>采样时间</th>
              <th>水温</th>
              <th>盐度</th>
              <th>DO</th>
              <th>pH</th>
              <th>备注</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={editingId === r.id ? 'row-editing' : ''}>
                <td>{r.id}</td>
                <td>{pondLabel(r.pondId)}</td>
                <td>{new Date(r.sampledAt).toLocaleString()}</td>
                <td>{r.tempC}</td>
                <td>{r.salinityPpt}</td>
                <td>{r.doMgL}</td>
                <td>{r.ph}</td>
                <td>{r.notes || '—'}</td>
                <td className="row-actions">
                  <button className="btn ghost" onClick={() => startEdit(r)}>
                    编辑
                  </button>
                  <button className="btn ghost" onClick={() => remove(r.id)}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
