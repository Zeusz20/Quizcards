// ask the user before leaving
var warn = true

window.onload = () => {
    window.addEventListener('beforeunload', (event) => {
        if(warn) {
            let msg = 'Are you sure you want to leave?'
            event.returnValue = msg
            window.event.returnValue = msg
            return msg
        }
    })
}

/* DECK EDITING OPTIONS */

updateDeleteButtons()   // update delete buttons

// add new card
document.getElementById('new-card').onclick = () => {
    const container = document.getElementById('container')
    let template = document.createElement('template')
    template.innerHTML = cardTemplate.trim()
    container.appendChild(template.content.firstChild)

    // update newly added delete button
    updateDeleteButtons()
}

function updateDeleteButtons() {
    document.getElementsByName('delete-btn').forEach(btn => {
        // prevents reassignment of the onclick function to delete buttons
        if(btn.onclick == null) {
            btn.onclick = () => {
                const card = btn.parentElement
                btn.parentElement.parentElement.removeChild(card)
            }
        }
    })
}

// preview uploaded term image
document.getElementsByName('term-image').forEach(file => {
    file.onchange = () => {
        // if file updloaded
        if(file.files) {
            // get corresponging image preview node
            const img = Array.from(file.parentElement.childNodes).filter(element => element.name == 'term-preview')[0]
            img.src = URL.createObjectURL(file.files[0])
        }
    }
})

// preview uploaded definition image
document.getElementsByName('definition-image').forEach(file => {
    file.onchange = () => {
        if(file.files) {
            const img = Array.from(file.parentElement.childNodes).filter(element => element.name == 'definition-preview')[0]
            img.src = URL.createObjectURL(file.files[0])
        }
    }
})

// delete image
document.getElementsByName('del-img').forEach(btn => {
    btn.onclick = () => {
        // get corresponding image input
        const file = Array.from(btn.parentElement.childNodes).filter(element => {
            return element.name == 'term-image' || element.name == 'definition-image'
        })[0]
        file.value = '';

        // remove preview image
        const img = Array.from(btn.parentElement.childNodes).filter(element => {
            return element.name == 'term-preview' || element.name == 'definition-preview'
        })[0]
        img.src = ''
    }
})


/* TEXT FORMATTING OPTIONS */

const tools = document.getElementsByName('tool');
const colorPickers = document.getElementsByName('picker')

// apply standard formatting options
tools.forEach(tool => {
    tool.addEventListener('click', () => {
        document.execCommand(tool.dataset['command'], false, null)
        
        // get neighboring element nodes
        let neighbors = Array.from(tool.parentElement.parentElement.childNodes).filter(item => {
            return item.nodeType == Node.ELEMENT_NODE   // filters out text nodes
        })
        
        // get corresponding editor to the clicked formatting button
        let editor = neighbors.filter(element => {
            let name = element.getAttribute('name')
            return name == 'term' || name == 'definition'
        })[0]

        editor.focus()
    })
})

// apply color
colorPickers.forEach(picker => {
    picker.addEventListener('change', () => {
        document.execCommand('styleWithCSS', false,  true)
        document.execCommand('foreColor', false, picker.value)
    })
})


/* SAVE AND LOAD */

// cannot save until user typed in deck's name
const deckName = document.getElementsByName('name')[0]
const saveBtn = document.getElementById('save-btn')

deckName.addEventListener('keyup', () => {
    saveBtn.disabled = (deckName.value === '')
})


// save deck
document.getElementById('save-btn').onclick = () => {
    warn = false

    // disable color pickers so they are not sent with POST
    Array.from(document.getElementsByTagName('input'))
        .filter(element => element.getAttribute('type') == 'color')
        .forEach(input => input.removeAttribute('name'))

    const form = document.getElementById('editor')
    addTextarea(form)   // saves formatted term and definition text data
    addImageIndexes()   // saves which image belongs to which term or definition
    form.submit()
}

/* This function adds textarea tags to the form with the corresponding div value. */
function addTextarea(form) {
    const terms = Array.from(document.getElementsByName('term'))
    const definitions = Array.from(document.getElementsByName('definition'))    
    const cards = terms.map((item, index) => {
        // zip terms and definitions
        return {
            'term': item, 
            'definition': definitions[index]
        }
    })

    cards.forEach(card => {
        let term = document.createElement('textarea')
        term.setAttribute('name', 'terms[]')
        term.innerHTML = card.term.innerHTML

        let definition = document.createElement('textarea')
        definition.setAttribute('name', 'definitions[]')
        definition.innerHTML = card.definition.innerHTML

        form.append(term, definition)
    })
}

/* This function handles the image indexes for the upload. */
function addImageIndexes() {
    const termWrappers = document.getElementsByName('term-image-wrapper')
    const definitionWrappers = document.getElementsByName('definition-image-wrapper')
    const syncValues = (wrapper) => {
        const children = Array.from(wrapper.childNodes).filter(node => {
            let isElementNode = (node.nodeType == Node.ELEMENT_NODE)
            let isInputTag = (node.tagName == 'INPUT')
            return isElementNode && isInputTag
        })
        
        children[0].value = getFileName(children[1].value)
    }

    termWrappers.forEach(syncValues)
    definitionWrappers.forEach(syncValues)
}

function getFileName(path) {    
    let startIndex = (path.indexOf('\\') >= 0 ? path.lastIndexOf('\\') : path.lastIndexOf('/'))
    let filename = path.substring(startIndex)
    if(filename.indexOf('\\') === 0 || filename.indexOf('/') === 0) {
        filename = filename.substring(1)
    }
    return filename
}