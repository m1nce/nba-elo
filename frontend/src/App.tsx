import { useEffect, useRef, useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Toaster } from '@/components/ui/sonner'
import { toast } from 'sonner'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import EloStandings from '@/pages/EloStandings'
import Matchup from '@/pages/Matchup'
import History from '@/pages/History'
import Upcoming from '@/pages/Upcoming'

export default function App() {
  const [refreshing, setRefreshing] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const queryClient = useQueryClient()

  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  useEffect(() => () => stopPolling(), [])

  async function handleRefresh() {
    setRefreshing(true)
    try {
      await api.refresh()
    } catch {
      toast.error('Failed to start refresh.')
      setRefreshing(false)
      return
    }

    pollRef.current = setInterval(async () => {
      try {
        const { running } = await api.refreshStatus()
        if (!running) {
          stopPolling()
          setRefreshing(false)
          queryClient.invalidateQueries()
          toast.success('Data refreshed.')
        }
      } catch {
        stopPolling()
        setRefreshing(false)
        toast.error('Lost contact with server during refresh.')
      }
    }, 2000)
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
          {refreshing && (
            <svg
              className="animate-spin h-4 w-4 mr-2"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z" />
            </svg>
          )}
          {refreshing ? 'Refreshing…' : 'Refresh Data'}
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
