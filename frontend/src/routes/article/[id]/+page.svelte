<script lang="ts">
	import type { PageData } from './$types';
	import { marked } from 'marked';
	
	let { data }: { data: PageData } = $props();

	let htmlContent = $state('');

	function parseCategories(categories: any) {
		if (!categories) return null;
		if (typeof categories === 'object') return categories;
		if (typeof categories === 'string') {
			try {
				const parsed = JSON.parse(categories);
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

	function formatDate(dateString: string | null) {
		if (!dateString) return 'Datum neznámé';
		const date = new Date(dateString);
		return date.toLocaleDateString('cs-CZ', { 
			year: 'numeric', 
			month: 'long', 
			day: 'numeric' 
		});
	}

	let parsedCategories = $derived(data.article ? parseCategories(data.article.categories) : null);
	
	$effect(() => {
		if (data.article?.content) {
			const result = marked.parse(data.article.content);
			if (typeof result === 'string') {
				htmlContent = result;
			} else {
				result.then((html: string) => {
					htmlContent = html;
				});
			}
		} else {
			htmlContent = '';
		}
	});
</script>

<div class="max-w-4xl mx-auto p-8">
	<a href="/" class="text-blue-600 hover:underline mb-6 inline-block">← Zpět na seznam</a>
	
	{#if data.error}
		<div class="bg-red-50 text-red-700 p-4 rounded">
			{data.error}
		</div>
	{:else if data.article}
		<article class="bg-white shadow-lg rounded-lg p-8">
			<header class="mb-6 border-b border-gray-200 pb-6">
				<h1 class="text-4xl font-bold text-gray-900 mb-3">{data.article.title}</h1>
				<div class="text-gray-600 text-sm">
					{formatDate(data.article.published_date)}
				</div>
				{#if data.article.url}
					<a 
						href={data.article.url} 
						target="_blank" 
						rel="noopener noreferrer"
						class="text-blue-600 hover:underline text-sm mt-2 inline-block"
					>
						Původní článek →
					</a>
				{/if}
			</header>

			{#if parsedCategories}
				<div class="bg-gray-50 p-4 rounded-lg mb-6">
					<h2 class="font-semibold text-gray-800 mb-2">Kategorie</h2>
					<div class="space-y-2 text-sm">
						{#if parsedCategories.what_happened}
							<div><span class="font-semibold">Co se stalo:</span> {parsedCategories.what_happened}</div>
						{/if}
						{#if parsedCategories.impact_on}
							<div><span class="font-semibold">Dopad na:</span> {parsedCategories.impact_on}</div>
						{/if}
						{#if parsedCategories.countries && Array.isArray(parsedCategories.countries) && parsedCategories.countries.length > 0}
							<div><span class="font-semibold">Země:</span> {parsedCategories.countries.join(', ')}</div>
						{/if}
						{#if parsedCategories.people && Array.isArray(parsedCategories.people) && parsedCategories.people.length > 0}
							<div><span class="font-semibold">Lidé:</span> {parsedCategories.people.join(', ')}</div>
						{/if}
					</div>
				</div>
			{/if}

			{#if htmlContent}
				<div class="text-gray-800 leading-relaxed [&_h1]:text-3xl [&_h1]:font-bold [&_h1]:mt-8 [&_h1]:mb-4 [&_h2]:text-2xl [&_h2]:font-bold [&_h2]:mt-6 [&_h2]:mb-3 [&_h3]:text-xl [&_h3]:font-semibold [&_h3]:mt-5 [&_h3]:mb-2 [&_p]:mb-4 [&_ul]:list-disc [&_ul]:list-inside [&_ul]:mb-4 [&_ul]:ml-4 [&_ol]:list-decimal [&_ol]:list-inside [&_ol]:mb-4 [&_ol]:ml-4 [&_li]:mb-2 [&_a]:text-blue-600 [&_a]:hover:underline [&_blockquote]:border-l-4 [&_blockquote]:border-gray-300 [&_blockquote]:pl-4 [&_blockquote]:italic [&_blockquote]:my-4 [&_code]:bg-gray-100 [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm [&_code]:font-mono [&_pre]:bg-gray-100 [&_pre]:p-4 [&_pre]:rounded [&_pre]:overflow-x-auto [&_pre]:mb-4 [&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_img]:max-w-full [&_img]:h-auto [&_img]:my-4 [&_img]:rounded [&_table]:w-full [&_table]:border-collapse [&_table]:mb-4 [&_th]:bg-gray-100 [&_th]:border [&_th]:border-gray-300 [&_th]:px-4 [&_th]:py-2 [&_th]:text-left [&_th]:font-semibold [&_td]:border [&_td]:border-gray-300 [&_td]:px-4 [&_td]:py-2">
					{@html htmlContent}
				</div>
			{:else}
				<p class="text-gray-500 italic">Obsah článku není k dispozici.</p>
			{/if}
		</article>
	{/if}
</div>
