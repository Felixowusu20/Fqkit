import { config, collection, fields } from '@keystatic/core'
import { FqkitMark } from './components/fqkit-mark.js'
import { block, inline, wrapper } from '@keystatic/core/content-components'

// Docs and tutorials use <Callout> in MDX. Keystatic refuses to open a page
// until every JSX component in the body has a matching definition.
const Callout = wrapper({
  label: 'Callout',
  schema: {
    type: fields.select({
      label: 'Type',
      options: [
        { label: 'Default', value: 'default' },
        { label: 'Info', value: 'info' },
        { label: 'Warning', value: 'warning' },
        { label: 'Error', value: 'error' },
        { label: 'Important', value: 'important' }
      ],
      defaultValue: 'default'
    })
  }
})

// Keystatic's MDX parser treats { } as JavaScript, so LaTeX cannot live in
// raw $$ blocks. These components keep the TeX in a quoted attribute.
const equationSchema = {
  tex: fields.text({
    label: 'LaTeX',
    multiline: true
  })
}

const Equation = block({
  label: 'Equation',
  schema: equationSchema
})

const Math = inline({
  label: 'Inline math',
  schema: equationSchema
})

const Circuit = block({
  label: 'Circuit diagram',
  schema: {
    spec: fields.text({
      label: 'Gates',
      description: 'One gate per line, or separated by semicolons. Example: H 0; CNOT 0 1',
      multiline: true
    }),
    caption: fields.text({
      label: 'Caption',
      validation: { isRequired: false }
    })
  }
})

const pageSchema = {
  title: fields.slug({
    name: {
      label: 'Title',
      validation: { isRequired: true }
    }
  }),
  description: fields.text({
    label: 'Description (shown in search results and SEO)',
    validation: { isRequired: false }
  }),
  body: fields.mdx({
    label: 'Content',
    components: { Callout, Equation, Math, Circuit }
  })
}

const collectionOptions = {
  format: { contentField: 'body' },
  slugField: 'title',
  schema: pageSchema
}

export default config({
  storage: { kind: 'local' },
  ui: {
    brand: { name: 'FQkit', mark: FqkitMark }
  },
  collections: {
    docs: collection({
      label: 'Docs pages',
      description: 'Reference pages under /docs',
      path: 'src/content/*',
      ...collectionOptions
    }),
    tutorials: collection({
      label: 'Tutorials',
      description: 'Teaching lessons under /docs/tutorials',
      path: 'src/content/tutorials/*',
      ...collectionOptions
    }),
    algorithms: collection({
      label: 'Algorithms',
      description: 'Algorithm lessons under /docs/algorithms',
      path: 'src/content/algorithms/*',
      ...collectionOptions
    }),
    applications: collection({
      label: 'Applications',
      description: 'Sector lessons under /docs/applications',
      path: 'src/content/applications/*',
      ...collectionOptions
    }),
    hardware: collection({
      label: 'Hardware',
      description: 'Runtime and job submission under /docs/hardware',
      path: 'src/content/hardware/*',
      ...collectionOptions
    }),
    notebooks: collection({
      label: 'Lessons',
      description: 'Practice lessons. Saving one publishes it in the sidebar on /notebooks.',
      path: 'src/notebooks/*',
      format: 'yaml',
      previewUrl: '/notebooks/{slug}',
      slugField: 'title',
      schema: {
        title: fields.slug({
          name: {
            label: 'Title',
            validation: { isRequired: true }
          }
        }),
        description: fields.text({
          label: 'Short description',
          validation: { isRequired: false }
        }),
        order: fields.integer({
          label: 'Order',
          defaultValue: 1,
          description: 'Lower numbers appear first in the lesson sidebar.'
        }),
        cells: fields.array(
          fields.object({
            kind: fields.select({
              label: 'Cell type',
              options: [
                { label: 'Text', value: 'markdown' },
                { label: 'Python', value: 'code' }
              ],
              defaultValue: 'code'
            }),
            source: fields.text({
              label: 'Cell contents',
              description: 'Text for a text cell, or Python for a code cell. In Python, show(qc) draws the circuit.',
              multiline: true
            })
          }),
          {
            label: 'Cells',
            itemLabel: props => (props.fields.kind.value === 'markdown' ? 'Text' : 'Python')
          }
        )
      }
    })
  }
})
