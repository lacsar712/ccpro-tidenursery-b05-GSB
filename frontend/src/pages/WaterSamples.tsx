import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Hatchery, Pond, WaterSample } from '../types'

function nowLocal() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
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
  const [hatcheries, setHatcheries] = useState<Hatchery[]>([])
  const [ponds, setPonds] = useState<Pond[]>([])
  const [rows, setRows] = useState<WaterSample[]>([])
  const [form, setForm] = useState(empty)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')

  async function load() {
    const [hs, ps, ws] = await Promise.all([
      api<Hatchery[]>('/api/hatcheries'),
      api<Pond[]>('/api/ponds'),
      api<WaterSample[]>('/api/water-samples'),
    ])
    setHatcheries(hs)
    setPonds(ps)
    setRows(ws)
    if (!form.pondId && ps[0]) {
      setForm((f) => ({ ...f, pondId: ps[0].id }))
    }
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const selectedPond = ponds.find((p) => p.id === form.pondId)
  const selectedHatchery = hatcheries.find(
    (h) => h.id === selectedPond?.hatcheryId,
  )
  const confirmationOpen = selectedHatchery?.sourceConfirmationOpen ?? false

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    const body: Record<string, unknown> = {
      ...form,
      sampledAt: new Date(form.sampledAt).toISOString(),
    }
    // 确认窗关闭后不再发送水源确认字段
    if (!confirmationOpen) delete body.sourceConfirmation
    try {
      if (editingId === null) {
        await api('/api/water-samples', { method: 'POST', body: JSON.stringify(body) })
      } else {
        const { pondId, ...updateBody } = body
        await api(`/api/water-samples/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify(updateBody),
        })
      }
      setForm((f) => ({ ...empty, pondId: f.pondId, sampledAt: nowLocal() }))
      setEditingId(null)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    }
  }

  function startEdit(r: WaterSample) {
    setEditingId(r.id)
    setError('')
    setForm({
      pondId: r.pondId,
      sampledAt: (() => {
        const d = new Date(r.sampledAt)
        d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
        return d.toISOString().slice(0, 16)
      })(),
      tempC: r.tempC,
      salinityPpt: r.salinityPpt,
      doMgL: r.doMgL,
      ph: r.ph,
      notes: r.notes || '',
      sourceConfirmation: '',
    })
  }

  function cancelEdit() {
    setEditingId(null)
    setForm((f) => ({ ...empty, pondId: f.pondId, sampledAt: nowLocal() }))
  }

  async function remove(id: number) {
    if (!confirm('确认删除该水质样？')) return
    try {
      await api(`/api/water-samples/${id}`, { method: 'DELETE' })
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
          校验：溶解氧 doMgL &gt; 0，pH ∈ [6, 9]；海水源切换后 24
          小时内须携带与新水源摘要一致的水源确认
        </p>
      </header>
      {error && <div className="error">{error}</div>}

      <form className="panel form-grid" onSubmit={onSubmit}>
        <label>
          塘口
          <select
            value={form.pondId}
            onChange={(e) => setForm({ ...form, pondId: Number(e.target.value) })}
            required
            disabled={editingId !== null}
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
        {confirmationOpen && (
          <label className="span-2">
            水源确认（该场处于 24 小时确认窗，须填写新水源摘要：
            {selectedHatchery?.seawaterSource}）
            <input
              value={form.sourceConfirmation}
              onChange={(e) =>
                setForm({ ...form, sourceConfirmation: e.target.value })
              }
              placeholder={selectedHatchery?.seawaterSource}
              required
            />
          </label>
        )}
        <label className="span-2">
          备注
          <input
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
          />
        </label>
        <div style={{ display: 'flex', gap: 10 }}>
          <button type="submit" className="btn primary">
            {editingId === null ? '登记水质样' : '保存修改'}
          </button>
          {editingId !== null && (
            <button type="button" className="btn ghost" onClick={cancelEdit}>
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
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{pondLabel(r.pondId)}</td>
                <td>{new Date(r.sampledAt).toLocaleString()}</td>
                <td>{r.tempC}</td>
                <td>{r.salinityPpt}</td>
                <td>{r.doMgL}</td>
                <td>{r.ph}</td>
                <td>{r.notes || '—'}</td>
                <td>
                  <button className="btn ghost" onClick={() => startEdit(r)}>
                    编辑
                  </button>{' '}
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
