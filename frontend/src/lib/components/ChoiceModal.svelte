<script lang="ts">
	import type { Choice, Card } from '$lib/game/types'
	import { game } from '$lib/stores/game.svelte'
	import CardComponent from './Card.svelte'

	interface Props {
		choice: Choice
		hand: Card[]
		supply: Record<string, { card: Card; count: number }>
	}

	let { choice, hand, supply }: Props = $props()

	let selected = $state<string[]>([])

	// Build the list of selectable options with card info where available
	const options = $derived(() => {
		return choice.valid_options.map(id => {
			// Check hand first
			const fromHand = hand.find(c => c.id === id)
			if (fromHand) return { id, card: fromHand, label: fromHand.name }
			// Check supply
			const fromSupply = supply[id]
			if (fromSupply) return { id, card: fromSupply.card, label: fromSupply.card.name }
			// Plain text option
			return { id, card: null as Card | null, label: id }
		})
	})

	const canConfirm = $derived(
		selected.length >= choice.min_selections &&
		selected.length <= choice.max_selections
	)

	function toggleSelect(id: string) {
		if (selected.includes(id)) {
			selected = selected.filter(s => s !== id)
		} else {
			// If max_selections === 1, replace selection
			if (choice.max_selections === 1) {
				selected = [id]
			} else if (selected.length < choice.max_selections) {
				selected = [...selected, id]
			}
		}
	}

	function confirm() {
		if (!canConfirm) return
		game.choose(selected)
		selected = []
	}

	function skip() {
		// Allow skipping if min_selections is 0
		if (choice.min_selections === 0) {
			game.choose([])
			selected = []
		}
	}
</script>

<div class="modal-overlay">
	<div class="modal">
		<div class="modal-header">
			<h2 class="modal-title">Choose</h2>
			<p class="modal-prompt">{choice.prompt}</p>
			{#if choice.min_selections !== choice.max_selections}
				<p class="modal-hint">
					Select {choice.min_selections === 0 ? 'up to' : 'between ' + choice.min_selections + ' and'}
					{choice.max_selections}
				</p>
			{:else if choice.max_selections > 1}
				<p class="modal-hint">Select exactly {choice.max_selections}</p>
			{/if}
		</div>

		<div class="modal-options">
			{#each options() as opt (opt.id)}
				{#if opt.card}
					<div
						class="option-card"
						class:selected={selected.includes(opt.id)}
						role="button"
						tabindex="0"
						onclick={() => toggleSelect(opt.id)}
						onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && toggleSelect(opt.id)}
					>
						<CardComponent
							card={opt.card}
							selected={selected.includes(opt.id)}
							playable
						/>
					</div>
				{:else}
					<button
						class="option-text"
						class:selected={selected.includes(opt.id)}
						onclick={() => toggleSelect(opt.id)}
					>
						{opt.label}
					</button>
				{/if}
			{/each}
		</div>

		<div class="modal-footer">
			{#if choice.min_selections === 0}
				<button class="btn-secondary" onclick={skip}>
					Skip
				</button>
			{/if}
			<button
				class="btn-primary confirm-btn"
				onclick={confirm}
				disabled={!canConfirm}
			>
				Confirm
				{#if selected.length > 0}
					({selected.length})
				{/if}
			</button>
		</div>
	</div>
</div>

<style>
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.75);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 100;
		padding: var(--space-md);
		backdrop-filter: blur(3px);
	}

	.modal {
		background: var(--bg-surface);
		border: 1px solid var(--border-strong);
		border-radius: var(--radius-md);
		max-width: 600px;
		width: 100%;
		max-height: 90dvh;
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
		overflow: hidden;
		box-shadow:
			0 20px 60px rgba(0, 0, 0, 0.8),
			0 0 0 1px rgba(201, 168, 76, 0.1);
		animation: modalIn 180ms ease-out;
	}

	@keyframes modalIn {
		from { opacity: 0; transform: scale(0.96) translateY(8px); }
		to { opacity: 1; transform: scale(1) translateY(0); }
	}

	.modal-header {
		padding: var(--space-lg) var(--space-lg) 0;
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
	}

	.modal-title {
		font-size: 1rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.modal-prompt {
		font-family: var(--font-heading);
		font-size: 1.1rem;
		color: var(--text);
		line-height: 1.3;
	}

	.modal-hint {
		font-size: 0.75rem;
		color: var(--text-muted);
		font-style: italic;
	}

	/* Options area */
	.modal-options {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-sm);
		padding: 0 var(--space-lg);
		overflow-y: auto;
		max-height: 60dvh;
		scrollbar-width: thin;
	}

	/* Card option */
	.option-card {
		cursor: pointer;
		outline: none;
		border-radius: var(--radius-card);
		transition: transform var(--transition-fast);
	}

	.option-card:hover {
		transform: translateY(-4px);
	}

	.option-card.selected {
		outline: 2px solid var(--accent);
		outline-offset: 2px;
	}

	/* Text option */
	.option-text {
		background: var(--bg-secondary);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: var(--space-sm) var(--space-md);
		font-size: 0.9rem;
		transition: background var(--transition-fast), border-color var(--transition-fast);
		cursor: pointer;
	}

	.option-text:hover {
		background: rgba(201, 168, 76, 0.08);
		border-color: var(--accent-dim);
	}

	.option-text.selected {
		background: rgba(201, 168, 76, 0.15);
		border-color: var(--accent);
		color: var(--accent);
	}

	/* Footer */
	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-sm);
		padding: 0 var(--space-lg) var(--space-lg);
		border-top: 1px solid var(--border);
		padding-top: var(--space-md);
	}

	.confirm-btn {
		min-width: 100px;
	}
</style>
