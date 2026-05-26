import { fontFamily } from 'tailwindcss/defaultTheme';

/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				brand: {
					purple: '#7C3AED',
					navy:   '#1E293B',
					green:  '#059669',
					ochre:  '#D97706',
				}
			},
			fontFamily: {
				sans: ['Inter', ...fontFamily.sans],
			},
			borderRadius: {
				'xl': '0.75rem',
				'2xl': '1rem',
			},
			boxShadow: {
				'card': '0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
				'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.06)',
			}
		}
	},
	plugins: []
};
