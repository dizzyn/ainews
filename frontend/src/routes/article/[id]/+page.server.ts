import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, fetch }) => {
	try {
		const response = await fetch(`http://backend:8000/articles/${params.id}`);
		
		if (!response.ok) {
			return {
				article: null,
				error: 'Článek nenalezen'
			};
		}
		
		const article = await response.json();
		
		return {
			article,
			error: null
		};
	} catch (error) {
		console.error('Chyba při načítání článku:', error);
		return {
			article: null,
			error: 'Nepodařilo se načíst článek'
		};
	}
};
