# Scaife Stack Backend

Backend / ATLAS implementation for the Scaife Stack prototype

This repository is powered by the [Scaife Viewer](https://scaife-viewer.org) project, an open-source ecosystem for building rich online reading environments.

## Getting Started

Make sure you are using a virtual environment of some sort (e.g. `virtualenv` or
`pyenv`).

```
pip install -r requirements-dev.txt
```

Retrieve content from the explorehomer-atlas repository:
```
./scripts/fetch-explorehomer-data.sh
```

Stage the ATLAS data directory:
```
python manage.py stage_atlas_data
```

Populate the database:

```
./manage.py prepare_atlas_db
./manage.py loaddata sites
```

Run the Django dev server:
```
./manage.py runserver
```

Browse to http://localhost:8000/.

Create a superuser:

```
./manage.py createsuperuser
```

Browse to `/admin/library/`

## Adding new text content
TODO: Write up the metadata spec and provide instructions.

See work done in https://github.com/scaife-viewer/beyond-translation-site/pull/126/files as a starting point.

Following the convention from that pull request, you would need to have directories, metadata JSON files and the flat text file organized in the structure below:
```shell
data/
├─ library/
│  ├─ <textgroup>/
│  │  ├─ metadata.json  # texgroup metadata
│  │  ├─ <work>/
│  │  │  ├─ metadata.json  # work and version metadata
│  │  │  ├─ <version>.txt  # version content
```

`<version>.txt` would contain content organized as follows:

```
<ref> <content>
```

The portion of the line before the first space is used as the text part reference.  Positions in the reference are separated with periods, e.g.:

- book 1 line  1 as 1.1
- page 1 as 1
- volume 1 page 1 section 1 as 1.1.1

Everything after the first space is considered the text part content.

For [urn:cts:greekLit:tlg0012.tlg001.parrish-eng1](https://github.com/scaife-viewer/beyond-translation-site/blob/ea234d9a352ca869281df7ce606b002e9cb0f742/backend/data/library/tlg0012/tlg001/tlg0012.tlg001.parrish-eng1.txt#L1)

```
1.1 Sing, goddess, the godlike wrath of Achilles, son of Peleus,
```

The ref is `1.1`.

The content is:
```
Sing, goddess, the godlike wrath of Achilles, son of Peleus,
```

## Sample Queries

Retrieve a list of versions.
```
{
  versions {
    edges {
      node {
        id
        urn
        metadata
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Retrieve the first version.
```
{
  versions(first: 1) {
    edges {
      node {
        metadata
      }
    }
  }
}
```

Retrieve books within a particular version.
```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:", rank: 1) {
    edges {
      node {
        ref
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Retrieve text part by its URN.
```
{
  textParts(urn: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1") {
    edges {
      node {
        ref
        textContent
      }
    }
  }
}
```

Retrieve tokens via a text part URN:
```
{
  tokens (textPart_Urn:"urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1") {
    edges {
      node {
        value
        uuid
        idx
        position
      }
    }
  }
}
```

Retrieve a passage by its URN along with relevant metadata.
```
{
  passageTextParts(reference: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1-2") {
    metadata
    edges {
      node {
        ref
        textContent
      }
    }
  }
}
```

Retrieve lines within a book within a particular version.
```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:2.", first: 5) {
    edges {
      node {
        ref
        textContent
      }
    }
  }
}
```

Retrieve lines and tokens within a book within a particular version.
```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:2.", first: 5) {
    edges {
      node {
        ref
        textContent
        tokens {
          edges {
            node {
              value
              idx
            }
          }
        }
      }
    }
  }
}
```

Page through text parts ten at a time.
```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:", rank: 2, first: 10) {
    edges {
      cursor
      node {
        id
        ref
        textContent
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

And then the next ten lines after that (use the `endCursor` value for `after`).

```
{
  textParts(urn_Startswith: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:", rank: 3, first: 10, after: "YXJyYXljb25uZWN0aW9uOjk=") {
    edges {
      cursor
      node {
        id
        label
        textContent
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Dump an entire `Node` tree rooted by URN and halting at `kind`. For example,
here we serialize all CTS URNs from their `NID` root up to (and including) the
level of `Version` nodes, maintaining the tree structure in the final payload.
```
{
  tree(urn: "urn:cts:", upTo: "version") {
    tree
  }
}
```

## Annotations

The annotations below are invoked by the `prepare_atlas_db` script.

While developing new annotations or ingesting data in alternate formats,
it can be helpful to run the annotation importer script in isolation
from `prepare_atlas_db`:

```python
from scaife_stack_atlas import importers

importers.text_annotations.import_text_annotations(reset=True)
```

### Text Alignments

#### Sample Queries

Get text alignment chunks for a given reference:
```
{
  textAlignmentChunks(reference: "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.8") {
    edges {
      cursor
      node {
        id
        citation
        items
        alignment {
          name
        }
      }
    }
  }
}
```

Get a version annotated with text alignment chunks:
```
{
  versions (urn:"urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:") {
    edges {
      node {
        metadata,
        textAlignmentChunks (first:2){
          edges {
            node {
              citation
            }
          }
        }
      }
    }
  }
}
```

### Named Entities

#### Sample Queries
Retrieve named entities
```
{
  namedEntities (first: 10) {
    edges {
      node {
        urn
        title
        description
        url
        tokens {
          edges {
            node {
              value
              textPart {
                urn
              }
            }
          }
        }
      }
    }
  }
}
```

Retrieve named entities for text part tokens
```
{
  tokens(textPart_Urn:"urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.16") {
    edges {
      node {
        value,
        namedEntities {
          edges {
            node {
              title
              description
              url
            }
          }
        }
      }
    }
  }
}
```

Retreive named entities given a passage reference
```
{
  namedEntities(reference:"urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7") {
    edges {
      node {
        id
        title
        description
        url
      }
    }
  }
}
```


## Tests

Invoke tests via:

```
pytest
```

## Transliteration

Transliteration requires installing the [PyICU](https://pypi.org/project/PyICU/) bindings.

See the documentation ["Installing PyICU"](https://gitlab.pyicu.org/main/pyicu#installing-pyicu) for additional instructions for your operating system.
