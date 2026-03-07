import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Badge } from '@/components/ui/badge'

export default function Upcoming() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['upcoming'],
    queryFn: api.upcoming,
    staleTime: 1000 * 60 * 30, // 30 min
  })

  if (isLoading) {
    return <div className="text-muted-foreground text-sm">Loading upcoming games…</div>
  }

  if (error) {
    return <div className="text-red-500 text-sm">Failed to load upcoming games.</div>
  }

  if (!data || data.length === 0) {
    return <div className="text-muted-foreground text-sm">No upcoming games found in the next 7 days.</div>
  }

  return (
    <div className="rounded border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b">
          <tr className="text-muted-foreground text-xs">
            <th className="py-2 px-3 text-left">Date</th>
            <th className="py-2 px-2 w-8" />
            <th className="py-2 text-left">Visitor</th>
            <th className="py-2 px-2 w-8" />
            <th className="py-2 text-left">Home</th>
            <th className="py-2 text-right">Visitor Win %</th>
            <th className="py-2 text-right px-3">Home Win %</th>
          </tr>
        </thead>
        <tbody>
          {data.map((game, i) => {
            const vFav = game.prob_v >= game.prob_h
            return (
              <tr key={i} className="border-b last:border-0 hover:bg-muted/40">
                <td className="py-2 px-3 text-muted-foreground whitespace-nowrap">{game.date}</td>
                <td className="py-2 px-2">
                  <img src={game.v_logo} alt={game.visitor} className="h-6 w-6 object-contain" />
                </td>
                <td className="py-2 font-medium">{game.visitor}</td>
                <td className="py-2 px-2">
                  <img src={game.h_logo} alt={game.home} className="h-6 w-6 object-contain" />
                </td>
                <td className="py-2 font-medium">{game.home}</td>
                <td className="py-2 text-right">
                  <Badge
                    variant={vFav ? 'default' : 'outline'}
                    className="text-xs"
                  >
                    {(game.prob_v * 100).toFixed(1)}%
                  </Badge>
                </td>
                <td className="py-2 text-right px-3">
                  <Badge
                    variant={!vFav ? 'default' : 'outline'}
                    className="text-xs"
                  >
                    {(game.prob_h * 100).toFixed(1)}%
                  </Badge>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
