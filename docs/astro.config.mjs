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
						href: '/gml2step/favicon.svg',
					},
				},
				{
					tag: 'meta',
					attrs: {
						name: 'robots',
						content: 'index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1',
					},
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:type',
						content: 'website',
					},
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:site_name',
						content: 'gml2step',
					},
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:image',
						content: 'https://soynyuu.github.io/gml2step/og-image.svg',
					},
				},
				{
					tag: 'meta',
					attrs: {
						name: 'twitter:card',
						content: 'summary_large_image',
					},
				},
				{
					tag: 'meta',
					attrs: {
						name: 'twitter:image',
						content: 'https://soynyuu.github.io/gml2step/og-image.svg',
					},
				},
				{
					tag: 'script',
					attrs: {
						type: 'application/ld+json',
					},
					content: JSON.stringify({
						'@context': 'https://schema.org',
						'@type': 'SoftwareApplication',
						name: 'gml2step',
						applicationCategory: 'DeveloperApplication',
						operatingSystem: 'Linux, macOS, Windows',
						programmingLanguage: 'Python',
						softwareVersion: '0.x',
						codeRepository: 'https://github.com/Soynyuu/gml2step',
						url: 'https://soynyuu.github.io/gml2step/',
						description: 'CityGML parser and STEP conversion toolkit for CAD/BIM workflows.',
					}),
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
