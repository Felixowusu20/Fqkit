import { config, collection, fields } from '@keystatic/core'

const pageSchema = {
  title: fields.text({
    label: 'Title',
    validation: { isRequired: true }
  }),
  description: fields.text({
    label: 'Description (shown in search results and SEO)',
    validation: { isRequired: false }
  }),
  body: fields.mdx({ label: 'Content' })
}

export default config({
  storage: { kind: 'local' },
  ui: {
    brand: { name: 'FQkit Docs' }
  },
  collections: {
    docs: collection({
      label: 'Docs pages',
      description: 'Reference pages under /docs',
      path: 'src/content/*',
      format: { contentField: 'body' },
      schema: pageSchema
    }),
    tutorials: collection({
      label: 'Tutorials',
      description: 'Teaching lessons under /docs/tutorials',
      path: 'src/content/tutorials/*',
      format: { contentField: 'body' },
      schema: pageSchema
    })
  }
})
