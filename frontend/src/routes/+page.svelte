<script lang="ts">
	import type { PageData } from './$types';
	
	export let data: PageData;

	function parseCategories(categories: any) {
		if (!categories) return null;
		if (typeof categories === 'object') return categories;
		if (typeof categories === 'string') {
			try {
				const parsed = JSON.parse(categories);
				// Validace struktury
				if (parsed && typeof parsed === 'object' && 
				    'what_happened' in parsed && 'impact_on' in parsed) {
					return parsed;
				}
				return null;
			} catch (e) {
				return null;
			}
		}
		return null;
	}
</script>

<div class="max-w-7xl mx-auto p-8">
	<h1 class="text-3xl font-bold mb-8 text-gray-800">Seznam článků</h1>
	
	{#if data.error}
		<p class="text-red-700 p-4 bg-red-50 rounded">{data.error}</p>
	{:else if !data.articles || data.articles.length === 0}
		<p class="text-gray-600">Zatím nejsou žádné články.</p>
	{:else}
		<div class="bg-white shadow rounded-lg overflow-hidden">
			<table class="w-full">
				<thead class="bg-gray-50">
					<tr>
						<th class="px-4 py-3 text-left font-semibold text-gray-700 border-b-2 border-gray-200">ID</th>
						<th class="px-4 py-3 text-left font-semibold text-gray-700 border-b-2 border-gray-200">Název</th>
						<th class="px-4 py-3 text-left font-semibold text-gray-700 border-b-2 border-gray-200">URL</th>
						<th class="px-4 py-3 text-left font-semibold text-gray-700 border-b-2 border-gray-200">Kategorie</th>
						<th class="px-4 py-3 text-left font-semibold text-gray-700 border-b-2 border-gray-200">Akce</th>
					</tr>
				</thead>
				<tbody>
					{#each data.articles as article}
						{@const parsed = parseCategories(article.categories)}
						{#if parsed}
							<tr class="hover:bg-gray-50 transition-colors">
								<td class="px-4 py-3 border-b border-gray-100">{article.id}</td>
								<td class="px-4 py-3 border-b border-gray-100">{article.title}</td>
								<td class="px-4 py-3 border-b border-gray-100">
									<a 
										href={article.url} 
										target="_blank" 
										rel="noopener noreferrer"
										class="text-blue-600 hover:underline"
									>
										{article.url}
									</a>
								</td>
								<td class="px-4 py-3 border-b border-gray-100">
									<div class="space-y-1 text-sm">
										{#if parsed.what_happened}
											<div><span class="font-semibold">Co se stalo:</span> {parsed.what_happened}</div>
										{/if}
										{#if parsed.impact_on}
											<div><span class="font-semibold">Dopad na:</span> {parsed.impact_on}</div>
										{/if}
										{#if parsed.countries && Array.isArray(parsed.countries) && parsed.countries.length > 0}
											<div><span class="font-semibold">Země:</span> {parsed.countries.join(', ')}</div>
										{/if}
										{#if parsed.people && Array.isArray(parsed.people) && parsed.people.length > 0}
											<div><span class="font-semibold">Lidé:</span> {parsed.people.join(', ')}</div>
										{/if}
									</div>
								</td>
								<td class="px-4 py-3 border-b border-gray-100">
									<a 
										href="/article/{article.id}" 
										class="text-blue-600 hover:underline font-medium"
									>
										Detail →
									</a>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
