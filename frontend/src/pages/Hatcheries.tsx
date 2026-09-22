import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Hatchery, SourceSwitch } from '../types'

const empty = { name: '', seawaterSource: '', notes: '' }

export default function Hatcheries() {
  const [rows, setRows] = useState<Hatchery[]>([])
  const [openCount, setOpenCount] = useState(0)
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [switchTarget, setSwitchTarget] = useState<Hatchery | null>(null)

  async function load() {
    const [data, count] = await Promise.all([
      api<Hatchery[]>('/api/hatcheries'),
      api<{ count: number }>('/api/hatcheries/source-confirmation-open-count'),
    ])
    setRows(data)
    setOpenCount(count.count)
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await api('/api/hatcheries', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setForm(empty)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    }
  }

  async function remove(id: number) {
    if (!confirm('确认删除该育苗场？')) return
    try {
      await api(`/api/hatcheries/${id}`, { method: 'DELETE' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  return (
    <div>
      <header className="page-header">
        <h1>育苗场</h1>
        <p className="muted">
          登记海水来源与场区备注 · 海水源变更必须登记切换日志，切换后 24 小时内下属塘口水质样需水源确认
        </p>
      </header>
      {error && <div className="error">{error}</div>}

      <div className="window-banner">
        开放水源确认窗场数：<strong>{openCount}</strong>
      </div>

      <form className="panel form-grid" onSubmit={onSubmit}>
        <label>
          名称
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
        </label>
        <label>
          海水来源
          <input
            value={form.seawaterSource}
            onChange={(e) => setForm({ ...form, seawaterSource: e.target.value })}
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
        <button type="submit" className="btn primary">
          新增育苗场
        </button>
      </form>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>海水来源</th>
              <th>水源确认窗</th>
              <th>备注</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.name}</td>
                <td>{r.seawaterSource}</td>
                <td>
                  {r.sourceConfirmationOpen ? (
                    <span className="badge window">确认中（24h）</span>
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
                <td>{r.notes || '—'}</td>
                <td className="row-actions">
                  <button className="btn ghost" onClick={() => setSwitchTarget(r)}>
                    水源切换
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

      {switchTarget && (
        <SwitchModal
          hatchery={switchTarget}
          onClose={() => setSwitchTarget(null)}
          onChanged={async () => {
            setSwitchTarget(null)
            await load()
          }}
        />
      )}
    </div>
  )
}

function SwitchModal({
  hatchery,
  onClose,
  onChanged,
}: {
  hatchery: Hatchery
  onClose: () => void
  onChanged: () => Promise<void>
}) {
  const [newSummary, setNewSummary] = useState('')
  const [logs, setLogs] = useState<SourceSwitch[] | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api<SourceSwitch[]>(`/api/hatcheries/${hatchery.id}/source-switches`)
      .then(setLogs)
      .catch((e) => setError(e.message))
  }, [hatchery.id])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await api(`/api/hatcheries/${hatchery.id}/source-switches`, {
        method: 'POST',
        body: JSON.stringify({ newSourceSummary: newSummary }),
      })
      await onChanged()
    } catch (err) {
      setError(err instanceof Error ? err.message : '切换失败')
      setBusy(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>{hatchery.name} · 海水源切换</h2>
          <button className="btn ghost" onClick={onClose}>
            关闭
          </button>
        </header>

        <div className="hint">
          当前海水源：<strong>{hatchery.seawaterSource}</strong>
          {hatchery.sourceConfirmationOpen && '（该场仍在 24 小时确认窗内）'}
        </div>

        {error && <div className="error">{error}</div>}

        <form className="form-stack switch-form" onSubmit={submit}>
          <label>
            新水源摘要（去空白后至少 4 字）
            <input
              value={newSummary}
              onChange={(e) => setNewSummary(e.target.value)}
              placeholder="例如：外海深管取水"
              required
              minLength={4}
            />
          </label>
          <button type="submit" className="btn primary" disabled={busy}>
            登记切换并更新场海水源
          </button>
        </form>

        <h3 className="modal-subtitle">切换日志</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>切换时刻</th>
                <th>旧水源摘要</th>
                <th>新水源摘要</th>
                <th>操作人</th>
              </tr>
            </thead>
            <tbody>
              {logs === null ? (
                <tr>
                  <td colSpan={4} className="muted">
                    加载中…
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="muted">
                    暂无切换记录
                  </td>
                </tr>
              ) : (
                logs.map((l) => (
                  <tr key={l.id}>
                    <td>{new Date(l.switchedAt).toLocaleString()}</td>
                    <td>{l.oldSourceSummary || '—'}</td>
                    <td>{l.newSourceSummary}</td>
                    <td>{l.operatorName}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
