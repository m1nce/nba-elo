import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Toaster } from '@/components/ui/sonner'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import EloStandings from '@/pages/EloStandings'
import Matchup from '@/pages/Matchup'
import History from '@/pages/History'
import Upcoming from '@/pages/Upcoming'

export default function App() {
  const [refreshing, setRefreshing] = useState(false)

  async function handleRefresh() {
    setRefreshing(true)
    try {
      const res = await api.refresh()
      toast.success(res.message ?? 'Refresh started.')
    } catch {
      toast.error('Failed to start refresh.')
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b px-6 py-3 flex items-center gap-6">
        <h1 className="font-oswald text-2xl tracking-widest">NBA ELO</h1>
        <Button
          variant="outline"
          size="sm"
          className="ml-auto"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          {refreshing ? 'Starting…' : 'Refresh Data'}
        </Button>
      </header>

      <main className="p-6">
        <Tabs defaultValue="standings">
          <TabsList className="mb-4">
            <TabsTrigger value="standings">ELO &amp; Standings</TabsTrigger>
            <TabsTrigger value="matchup">Match-up</TabsTrigger>
            <TabsTrigger value="history">Match History</TabsTrigger>
            <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
          </TabsList>

          <TabsContent value="standings"><EloStandings /></TabsContent>
          <TabsContent value="matchup"><Matchup /></TabsContent>
          <TabsContent value="history"><History /></TabsContent>
          <TabsContent value="upcoming"><Upcoming /></TabsContent>
        </Tabs>
      </main>

      <Toaster />
    </div>
  )
}
