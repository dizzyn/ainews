import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, fetch }) => {
	try {
		const response = await fetch(`http://backend:8000/articles/${params.id}`);
		
		if (!response.ok) {
			return {
				article: null,
				relatedArticles: [],
				error: 'Článek nenalezen'
			};
		}
		
		const article = await response.json();
		
		// Načteme související články
		let relatedArticles = [];
		try {
			const relatedResponse = await fetch(`http://backend:8000/articles/${params.id}/related?limit=5`);
			if (relatedResponse.ok) {
				relatedArticles = await relatedResponse.json();
			}
		} catch (e) {
			console.error('Chyba při načítání souvisejících článků:', e);
		}
		
		return {
			article,
			relatedArticles,
			error: null
		};
	} catch (error) {
		console.error('Chyba při načítání článku:', error);
		return {
			article: null,
			relatedArticles: [],
			error: 'Nepodařilo se načíst článek'
		};
	}
};
