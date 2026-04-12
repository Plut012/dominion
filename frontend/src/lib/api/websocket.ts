import type { ClientMessage, ServerMessage } from '$lib/game/types'

type MessageHandler = (msg: ServerMessage) => void
type ConnectionHandler = (connected: boolean) => void

export class GameSocket {
  private ws: WebSocket | null = null
  private onMessage: MessageHandler
  private onConnection: ConnectionHandler
  private url: string
  private reconnected = false

  constructor(onMessage: MessageHandler, onConnection: ConnectionHandler) {
    this.onMessage = onMessage
    this.onConnection = onConnection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    this.url = `${protocol}//${window.location.hostname}:8000/ws`
  }

  connect(): void {
    this.reconnected = false
    this._open()
  }

  private _open(): void {
    const ws = new WebSocket(this.url)
    this.ws = ws

    ws.onopen = () => {
      this.onConnection(true)
    }

    ws.onmessage = (event: MessageEvent) => {
      let msg: ServerMessage
      try {
        msg = JSON.parse(event.data as string) as ServerMessage
      } catch {
        console.error('GameSocket: failed to parse message', event.data)
        return
      }
      this.onMessage(msg)
    }

    ws.onclose = () => {
      this.onConnection(false)
      if (!this.reconnected) {
        this.reconnected = true
        this._open()
      }
    }

    ws.onerror = (event: Event) => {
      console.error('GameSocket: error', event)
    }
  }

  send(msg: ClientMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg))
    } else {
      console.warn('GameSocket: send called while not connected', msg)
    }
  }

  disconnect(): void {
    this.reconnected = true // prevent auto-reconnect
    if (this.ws) {
      this.ws.onclose = null
      this.ws.close()
      this.ws = null
    }
    this.onConnection(false)
  }
}
