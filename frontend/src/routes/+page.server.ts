import type { PageServerLoad } from './$types';

const API_URL = 'http://backend:8000';

export const load: PageServerLoad = async () => {
	try {
		const response = await fetch(`${API_URL}/articles/`);
		
		if (!response.ok) {
			console.error('API response not OK:', response.status, response.statusText);
			return {
				articles: [],
				error: 'Nepodařilo se načíst články'
			};
		}
		
		const articles = await response.json();
		
		return {
			articles: articles || []
		};
	} catch (error) {
		console.error('Error loading articles:', error);
		return {
			articles: [],
			error: `Chyba při načítání článků: ${error instanceof Error ? error.message : 'Neznámá chyba'}`
		};
	}
};
