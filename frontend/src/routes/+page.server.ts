import type { PageServerLoad } from './$types';

const API_URL = 'http://backend:8000';

export const load: PageServerLoad = async () => {
	try {
		// Načteme digest
		let digest = null;
		try {
			const digestResponse = await fetch(`${API_URL}/digest/`);
			if (digestResponse.ok) {
				digest = await digestResponse.json();
			}
		} catch (e) {
			console.log('Digest not available yet');
		}

		// Načteme články
		const response = await fetch(`${API_URL}/articles/`);
		
		if (!response.ok) {
			console.error('API response not OK:', response.status, response.statusText);
			return {
				articles: [],
				digest: null,
				error: 'Nepodařilo se načíst články'
			};
		}
		
		const articles = await response.json();
		
		return {
			articles: articles || [],
			digest
		};
	} catch (error) {
		console.error('Error loading articles:', error);
		return {
			articles: [],
			digest: null,
			error: `Chyba při načítání článků: ${error instanceof Error ? error.message : 'Neznámá chyba'}`
		};
	}
};
