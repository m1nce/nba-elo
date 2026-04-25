import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts'
import { ChartContainer } from '@/components/ui/chart'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Check, Search } from 'lucide-react'
import type { GameRow } from '@/lib/types'

const FILTERS = [
  { label: 'Current Season', value: 'season' as const },
  { label: 'Last 5',         value: 5 },
  { label: 'Last 10',        value: 10 },
  { label: 'Last 20',        value: 20 },
  { label: 'All',            value: 0 },
]

const TEAM_DATA = [
  // East — Atlantic
  { name: 'Boston Celtics',          abbrev: 'bos',  conf: 'E' as const },
  { name: 'Brooklyn Nets',           abbrev: 'bkn',  conf: 'E' as const },
  { name: 'New York Knicks',         abbrev: 'nyk',  conf: 'E' as const },
  { name: 'Philadelphia 76ers',      abbrev: 'phi',  conf: 'E' as const },
  { name: 'Toronto Raptors',         abbrev: 'tor',  conf: 'E' as const },
  // East — Central
  { name: 'Chicago Bulls',           abbrev: 'chi',  conf: 'E' as const },
  { name: 'Cleveland Cavaliers',     abbrev: 'cle',  conf: 'E' as const },
  { name: 'Detroit Pistons',         abbrev: 'det',  conf: 'E' as const },
  { name: 'Indiana Pacers',          abbrev: 'ind',  conf: 'E' as const },
  { name: 'Milwaukee Bucks',         abbrev: 'mil',  conf: 'E' as const },
  // East — Southeast
  { name: 'Atlanta Hawks',           abbrev: 'atl',  conf: 'E' as const },
  { name: 'Charlotte Hornets',       abbrev: 'cha',  conf: 'E' as const },
  { name: 'Miami Heat',              abbrev: 'mia',  conf: 'E' as const },
  { name: 'Orlando Magic',           abbrev: 'orl',  conf: 'E' as const },
  { name: 'Washington Wizards',      abbrev: 'wsh',  conf: 'E' as const },
  // West — Northwest
  { name: 'Denver Nuggets',          abbrev: 'den',  conf: 'W' as const },
  { name: 'Minnesota Timberwolves',  abbrev: 'min',  conf: 'W' as const },
  { name: 'Oklahoma City Thunder',   abbrev: 'okc',  conf: 'W' as const },
  { name: 'Portland Trail Blazers',  abbrev: 'por',  conf: 'W' as const },
  { name: 'Utah Jazz',               abbrev: 'utah', conf: 'W' as const },
  // West — Pacific
  { name: 'Golden State Warriors',   abbrev: 'gsw',  conf: 'W' as const },
  { name: 'Los Angeles Clippers',    abbrev: 'lac',  conf: 'W' as const },
  { name: 'Los Angeles Lakers',      abbrev: 'lal',  conf: 'W' as const },
  { name: 'Phoenix Suns',            abbrev: 'phx',  conf: 'W' as const },
  { name: 'Sacramento Kings',        abbrev: 'sac',  conf: 'W' as const },
  // West — Southwest
  { name: 'Dallas Mavericks',        abbrev: 'dal',  conf: 'W' as const },
  { name: 'Houston Rockets',         abbrev: 'hou',  conf: 'W' as const },
  { name: 'Memphis Grizzlies',       abbrev: 'mem',  conf: 'W' as const },
  { name: 'New Orleans Pelicans',    abbrev: 'no',   conf: 'W' as const },
  { name: 'San Antonio Spurs',       abbrev: 'sas',  conf: 'W' as const },
]

function logoUrl(abbrev: string) {
  return `https://a.espncdn.com/i/teamlogos/nba/500/${abbrev}.png`
}

// ── Team Combobox ────────────────────────────────────────────────────────────

function TeamCombobox({
  label,
  value,
  onChange,
  exclude,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  exclude?: string
}) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')

  const filtered = TEAM_DATA.filter(
    t => t.name !== exclude && t.name.toLowerCase().includes(search.toLowerCase())
  )
  const selected = TEAM_DATA.find(t => t.name === value)

  function handleOpenChange(o: boolean) {
    setOpen(o)
    if (!o) setSearch('')
  }

  return (
    <div className="flex-1">
      <p className="text-xs text-muted-foreground mb-1 font-medium tracking-widest uppercase">
        {label}
      </p>
      <Popover open={open} onOpenChange={handleOpenChange}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between h-10 px-3 transition-all"
          >
            <span className="flex items-center gap-2 min-w-0">
              {selected && (
                <img
                  src={logoUrl(selected.abbrev)}
                  alt={selected.name}
                  className="h-5 w-5 object-contain shrink-0"
                />
              )}
              <span className="truncate text-sm">{value}</span>
            </span>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[260px] p-0" align="start">
          <div className="flex items-center border-b px-3">
            <Search className="mr-2 h-4 w-4 shrink-0 opacity-40" />
            <input
              autoFocus
              className="flex h-10 w-full bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground"
              placeholder="Search teams…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div className="max-h-64 overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <p className="px-3 py-4 text-sm text-muted-foreground text-center">No team found.</p>
            ) : (
              filtered.map(t => (
                <button
                  key={t.name}
                  onClick={() => { onChange(t.name); setOpen(false); setSearch('') }}
                  className={`flex items-center gap-2.5 w-full px-3 py-2 text-sm hover:bg-accent text-left transition-colors ${
                    t.name === value ? 'bg-accent/50' : ''
                  }`}
                >
                  <img
                    src={logoUrl(t.abbrev)}
                    alt={t.name}
                    className="h-6 w-6 object-contain shrink-0"
                  />
                  <span className="flex-1">{t.name}</span>
                  {t.name === value && <Check className="h-3.5 w-3.5 opacity-60 shrink-0" />}
                </button>
              ))
            )}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}

// ── Game Log Row ─────────────────────────────────────────────────────────────

function GameLogRow({ game }: { game: GameRow }) {
  const visitorWon = game.result === 'visitor'
  return (
    <tr className="border-b last:border-0 hover:bg-muted/40 text-sm">
      <td className="py-1.5 text-muted-foreground">{game.date}</td>
      <td className={`py-1.5 font-medium ${visitorWon ? 'text-foreground' : 'text-muted-foreground'}`}>
        {game.visitor}
      </td>
      <td className={`py-1.5 font-medium ${!visitorWon ? 'text-foreground' : 'text-muted-foreground'}`}>
        {game.home}
      </td>
      <td className="py-1.5 text-center">
        {game.visitor_points} – {game.home_points}
      </td>
      <td className={`py-1.5 text-right text-xs ${(game.visitor_delta ?? 0) >= 0 ? 'text-green-600' : 'text-red-500'}`}>
        {(game.visitor_delta ?? 0) >= 0 ? '+' : ''}{(game.visitor_delta ?? 0).toFixed(1)}
      </td>
      <td className="py-1.5 text-right text-xs text-muted-foreground">
        {game.win_prob_visitor != null ? `${(game.win_prob_visitor * 100).toFixed(1)}%` : '—'}
      </td>
      <td className="py-1.5 text-right text-xs text-muted-foreground">{game.notes ?? ''}</td>
    </tr>
  )
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function Matchup() {
  const [visitor, setVisitor] = useState('Los Angeles Lakers')
  const [home, setHome]       = useState('Boston Celtics')
  const [filter, setFilter]   = useState<'season' | number>('season')

  const apiFilter = filter === 'season' ? 0 : filter

  const { data, isLoading, error } = useQuery({
    queryKey: ['matchup', visitor, home, apiFilter],
    queryFn: () => api.matchup(visitor, home, apiFilter),
    enabled: visitor !== home,
  })

  const lowPct  = data ? Math.max(0,   data.prob_v * 100 - 10) : 40
  const highPct = data ? Math.min(100, data.prob_v * 100 + 10) : 60
  const gradientStyle = data
    ? `linear-gradient(90deg, ${data.v_color}bb 0%, ${data.v_color}33 ${lowPct.toFixed(1)}%, ${data.h_color}33 ${highPct.toFixed(1)}%, ${data.h_color}bb 100%)`
    : 'linear-gradient(90deg, #eee 0%, #eee 100%)'

  const seasonStart = useMemo(() => {
    const allDates = [
      ...(data?.elo_history_v ?? []).map(p => p.date),
      ...(data?.h2h_games ?? []).map(g => g.date),
    ]
    if (!allDates.length) return null
    const last = allDates.sort().at(-1)!
    const y = parseInt(last.slice(0, 4))
    const m = parseInt(last.slice(5, 7))
    return `${m >= 10 ? y : y - 1}-10`
  }, [data])

  const filteredGames = useMemo(() => {
    if (!data) return []
    if (filter === 'season' && seasonStart)
      return data.h2h_games.filter(g => g.date >= seasonStart)
    return data.h2h_games
  }, [data, filter, seasonStart])

  const chartData = useMemo(() => {
    if (!data) return []
    const byDate = new Map<string, Record<string, number | string>>()
    for (const pt of data.elo_history_v) {
      byDate.set(pt.date, { date: pt.date, [visitor]: pt.elo })
    }
    for (const pt of data.elo_history_h) {
      const row = byDate.get(pt.date) ?? { date: pt.date }
      row[home] = pt.elo
      byDate.set(pt.date, row)
    }
    const sorted = Array.from(byDate.values()).sort((a, b) =>
      String(a.date).localeCompare(String(b.date))
    )
    if (filter === 'season') {
      return seasonStart ? sorted.filter(r => String(r.date) >= seasonStart) : sorted
    }
    if (filter > 0) {
      const anchorDate = filteredGames.at(-1)?.date
      if (!anchorDate) return sorted
      return sorted.filter(r => String(r.date) >= anchorDate)
    }
    return sorted
  }, [data, visitor, home, filter, seasonStart, filteredGames])

  return (
    <div className="space-y-4">
      {/* Team comboboxes */}
      <div className="flex items-end gap-4">
        <TeamCombobox
          label="Visitor"
          value={visitor}
          onChange={setVisitor}
          exclude={home}
        />
        <div className="font-oswald text-xl text-muted-foreground mb-2 shrink-0">VS</div>
        <TeamCombobox
          label="Home"
          value={home}
          onChange={setHome}
          exclude={visitor}
        />
      </div>

      {/* Filter buttons */}
      <div className="flex gap-1 justify-center">
        <span className="text-sm text-muted-foreground self-center mr-2">Show:</span>
        {FILTERS.map(f => (
          <Button
            key={String(f.value)}
            size="sm"
            variant={filter === f.value ? 'default' : 'outline'}
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </Button>
        ))}
      </div>

      {visitor === home && (
        <p className="text-muted-foreground text-sm">Select two different teams.</p>
      )}

      {isLoading && visitor !== home && (
        <div className="text-muted-foreground text-sm">Loading matchup…</div>
      )}

      {error && (
        <div className="text-red-500 text-sm">Failed to load matchup data.</div>
      )}

      {data && (
        <>
          {/* Win probability card + ELO chart */}
          <div className="flex gap-4 items-stretch">
            <div
              className="w-[38%] flex-none rounded-xl border p-5 flex items-center"
              style={{ background: gradientStyle }}
            >
              <div className="text-center flex-1 min-w-0">
                <img src={data.v_logo} alt={data.visitor} className="h-16 mx-auto mb-3"
                  style={{ filter: `drop-shadow(0 0 8px ${data.v_color}55)` }} />
                <div className="font-oswald text-4xl font-black" style={{ color: data.v_color }}>
                  {(data.prob_v * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-muted-foreground mt-1 tracking-widest uppercase">
                  Visitor · ELO {data.r_v.toFixed(0)}
                </div>
                <div className="text-sm font-semibold mt-1">{data.visitor}</div>
              </div>

              <div className="text-center px-5 shrink-0">
                <div className="font-oswald text-lg font-black text-muted-foreground/50 tracking-widest">VS</div>
                <div className="w-px h-10 bg-gradient-to-b from-transparent via-border to-transparent mx-auto my-2" />
                <div className="text-[10px] text-muted-foreground/60 tracking-wide uppercase leading-snug">
                  Home Court<br />+100 ELO
                </div>
              </div>

              <div className="text-center flex-1 min-w-0">
                <img src={data.h_logo} alt={data.home} className="h-16 mx-auto mb-3"
                  style={{ filter: `drop-shadow(0 0 8px ${data.h_color}55)` }} />
                <div className="font-oswald text-4xl font-black" style={{ color: data.h_color }}>
                  {(data.prob_h * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-muted-foreground mt-1 tracking-widest uppercase">
                  Home · ELO {data.r_h.toFixed(0)}
                </div>
                <div className="text-sm font-semibold mt-1">{data.home}</div>
              </div>
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted-foreground tracking-widest uppercase mb-2">ELO Rating History</p>
              <ChartContainer config={{}} className="h-[260px] w-full">
                <LineChart data={chartData} margin={{ left: 10, right: 10, top: 10, bottom: 10 }}>
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickLine={false} axisLine={false}
                    interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={40} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null
                      return (
                        <div className="rounded border bg-background px-2 py-1 text-xs shadow space-y-0.5">
                          {payload.map(pt => (
                            <div key={pt.name}>
                              <span className="font-medium" style={{ color: pt.color as string }}>{pt.name}</span>
                              <span className="ml-2 text-muted-foreground">{Number(pt.value).toFixed(1)}</span>
                            </div>
                          ))}
                        </div>
                      )
                    }}
                  />
                  <Line type="monotone" dataKey={visitor} stroke={data.v_color} dot={false} strokeWidth={2} isAnimationActive={false} connectNulls />
                  <Line type="monotone" dataKey={home} stroke={data.h_color} dot={false} strokeWidth={2} isAnimationActive={false} connectNulls />
                </LineChart>
              </ChartContainer>
            </div>
          </div>

          {/* Record banner */}
          <div
            className="rounded-xl border p-5 flex items-center justify-between"
            style={{
              background: `linear-gradient(90deg, ${data.v_color}11 0%, #f5f5f5 40%, #f5f5f5 60%, ${data.h_color}11 100%)`,
            }}
          >
            <div className="text-center flex-1">
              <img src={data.v_logo} alt={data.visitor} className="h-12 mx-auto mb-1"
                style={{ filter: `drop-shadow(0 0 6px ${data.v_color}55)` }} />
              <div className="font-oswald text-sm text-muted-foreground tracking-wide">{data.visitor}</div>
            </div>
            <div className="text-center px-6">
              <div className="font-oswald text-4xl font-bold tracking-widest">
                {filteredGames.filter(g =>
                  (g.visitor === visitor && g.result === 'visitor') ||
                  (g.home === visitor && g.result === 'home')
                ).length}
                {' – '}
                {filteredGames.filter(g =>
                  (g.visitor === home && g.result === 'visitor') ||
                  (g.home === home && g.result === 'home')
                ).length}
              </div>
              <div className="text-[10px] text-muted-foreground tracking-widest uppercase mt-1">
                {filter === 'season' ? 'Current Season' : data.record_label}
              </div>
            </div>
            <div className="text-center flex-1">
              <img src={data.h_logo} alt={data.home} className="h-12 mx-auto mb-1"
                style={{ filter: `drop-shadow(0 0 6px ${data.h_color}55)` }} />
              <div className="font-oswald text-sm text-muted-foreground tracking-wide">{data.home}</div>
            </div>
          </div>

          {/* H2H game log */}
          {filteredGames.length === 0 ? (
            <p className="text-muted-foreground text-sm">No games found between these teams.</p>
          ) : (
            <ScrollArea className="h-80 rounded border">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-background border-b">
                  <tr className="text-muted-foreground text-xs">
                    <th className="py-2 text-left pl-2">Date</th>
                    <th className="py-2 text-left">Visitor</th>
                    <th className="py-2 text-left">Home</th>
                    <th className="py-2 text-center">Score</th>
                    <th className="py-2 text-right">V ELO Δ</th>
                    <th className="py-2 text-right">Win Prob</th>
                    <th className="py-2 text-right pr-2">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredGames.map(g => <GameLogRow key={g.id} game={g} />)}
                </tbody>
              </table>
            </ScrollArea>
          )}
        </>
      )}
    </div>
  )
}
