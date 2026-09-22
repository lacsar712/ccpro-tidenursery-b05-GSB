import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Hatchery, OpenConfirmCount, SourceSwitchLog } from '../types'

const empty = { name: '', seawaterSource: '', notes: '' }
const switchEmpty = { hatcheryId: 0, newSourceSummary: '', operatorName: '' }

export default function Hatcheries() {
  const [rows, setRows] = useState<Hatchery[]>([])
  const [logs, setLogs] = useState<SourceSwitchLog[]>([])
  const [openCount, setOpenCount] = useState(0)
  const [form, setForm] = useState(empty)
  const [switchForm, setSwitchForm] = useState(switchEmpty)
  const [error, setError] = useState('')
  const [switchError, setSwitchError] = useState('')

  async function load() {
    const [hs, count, switchLogs] = await Promise.all([
      api<Hatchery[]>('/api/hatcheries'),
      api<OpenConfirmCount>('/api/hatcheries/source-confirmations/open-count'),
      api<SourceSwitchLog[]>('/api/source-switches').catch(() => [] as SourceSwitchLog[]),
    ])
    setRows(hs)
    setOpenCount(count.openCount)
    setLogs(switchLogs)
    if (!switchForm.hatcheryId && hs[0]) {
      setSwitchForm((f) => ({ ...f, hatcheryId: hs[0].id }))
    }
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  async function onSwitch(e: FormEvent) {
    e.preventDefault()
    setSwitchError('')
    try {
      await api(
        `/api/hatcheries/${switchForm.hatcheryId}/source-switches`,
        {
          method: 'POST',
          body: JSON.stringify({
            newSourceSummary: switchForm.newSourceSummary,
            operatorName: switchForm.operatorName,
          }),
        },
      )
      setSwitchForm((f) => ({ ...f, newSourceSummary: '' }))
      await load()
    } catch (err) {
      setSwitchError(err instanceof Error ? err.message : '切换登记失败')
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

  const hatcheryName = (id: number) =>
    rows.find((h) => h.id === id)?.name || `#${id}`

  return (
    <div>
      <header className="page-header">
        <h1>育苗场</h1>
        <p className="muted">
          登记海水来源与场区备注；海水源变更必须登记切换日志
        </p>
      </header>
      {error && <div className="error">{error}</div>}

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(3, minmax(0,1fr))' }}>
        <div className="stat-card">
          <div className="stat-label">育苗场总数</div>
          <div className="stat-value">{rows.length}</div>
        </div>
        <div className={`stat-card${openCount > 0 ? ' warn' : ''}`}>
          <div className="stat-label">水源确认窗开放中场数</div>
          <div className="stat-value">{openCount}</div>
        </div>
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
                    <span className="badge quarantine">确认窗内（24h）</span>
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
                <td>{r.notes || '—'}</td>
                <td>
                  <button className="btn ghost" onClick={() => remove(r.id)}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 style={{ marginTop: 28 }}>海水源切换登记</h2>
      <p className="hint">
        切换成功后将同事务写入切换日志并更新育苗场海水源字段；切换时刻起 24
        小时内，该场塘口新建或更新水质样必须携带与新水源摘要一致的水源确认。
      </p>
      {switchError && <div className="error">{switchError}</div>}
      <form className="panel form-grid" onSubmit={onSwitch}>
        <label>
          所属育苗场
          <select
            value={switchForm.hatcheryId}
            onChange={(e) =>
              setSwitchForm({ ...switchForm, hatcheryId: Number(e.target.value) })
            }
            required
          >
            {rows.map((h) => (
              <option key={h.id} value={h.id}>
                {h.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          操作人
          <input
            value={switchForm.operatorName}
            onChange={(e) =>
              setSwitchForm({ ...switchForm, operatorName: e.target.value })
            }
            placeholder="操作人姓名"
            required
          />
        </label>
        <label className="span-2">
          新水源摘要（去空白后至少 4 个字）
          <input
            value={switchForm.newSourceSummary}
            onChange={(e) =>
              setSwitchForm({ ...switchForm, newSourceSummary: e.target.value })
            }
            placeholder="例如：外海深管抽海水"
            required
          />
        </label>
        <button type="submit" className="btn primary">
          登记切换
        </button>
      </form>

      <h2 style={{ marginTop: 28 }}>切换日志</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>所属育苗场</th>
              <th>切换时刻</th>
              <th>旧水源摘要</th>
              <th>新水源摘要</th>
              <th>操作人</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  暂无切换日志
                </td>
              </tr>
            )}
            {logs.map((l) => (
              <tr key={l.id}>
                <td>{hatcheryName(l.hatcheryId)}</td>
                <td>{new Date(l.switchedAt).toLocaleString()}</td>
                <td>{l.oldSourceSummary || '—'}</td>
                <td>{l.newSourceSummary}</td>
                <td>{l.operatorName}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
