// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
	site: 'https://soynyuu.github.io',
	base: '/gml2step',
	integrations: [
		starlight({
			title: 'gml2step',
			defaultLocale: 'en',
			locales: {
				en: { label: 'English', lang: 'en' },
				ja: { label: '日本語', lang: 'ja' },
			},
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/Soynyuu/gml2step' },
			],
			sidebar: [
				{
					label: 'Getting Started',
					translations: { ja: 'はじめに' },
					items: [
						{ slug: 'installation', label: 'Installation', translations: { ja: 'インストール' } },
					],
				},
				{
					label: 'Reference',
					translations: { ja: 'リファレンス' },
					items: [
						{ slug: 'cli', label: 'CLI', translations: { ja: 'CLI' } },
						{ slug: 'api', label: 'Python API', translations: { ja: 'Python API' } },
						{ slug: 'configuration', label: 'Configuration', translations: { ja: '設定' } },
					],
				},
				{
					label: 'Guides',
					translations: { ja: 'ガイド' },
					items: [
						{ slug: 'conversion', label: 'Conversion', translations: { ja: '変換' } },
						{ slug: 'plateau', label: 'PLATEAU', translations: { ja: 'PLATEAU' } },
					],
				},
				{
					label: 'Internals',
					translations: { ja: '内部構造' },
					items: [
						{ slug: 'architecture', label: 'Architecture', translations: { ja: 'アーキテクチャ' } },
						{ slug: 'development', label: 'Development', translations: { ja: '開発' } },
					],
				},
			],
			customCss: ['./src/styles/custom.css'],
			head: [
				{
					tag: 'link',
					attrs: {
						rel: 'icon',
						type: 'image/svg+xml',
						href: '/favicon.svg',
					},
				},
				{
					tag: 'link',
					attrs: {
						rel: 'preconnect',
						href: 'https://fonts.googleapis.com',
					},
				},
				{
					tag: 'link',
					attrs: {
						rel: 'preconnect',
						href: 'https://fonts.gstatic.com',
						crossorigin: '',
					},
				},
				{
					tag: 'link',
					attrs: {
						rel: 'stylesheet',
						href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+JP:wght@300;400;500;600&display=swap',
					},
				},
			],
		}),
	],
});
