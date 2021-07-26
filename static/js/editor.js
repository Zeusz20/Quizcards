// ask the user before leaving
var warn = true

// start editor
init()


function init() {
    window.onload = warnUser

    if(rawDeck !== '' && rawCards !== '') {
        const deck = JSON.parse(rawDeck)
        const cards = JSON.parse(rawCards)
        load(deck, cards)
    }

    updateButtons()
}

function warnUser() {
    window.addEventListener('beforeunload', (event) => {
        if(warn) {
            let msg = 'Are you sure you want to leave?'
            event.returnValue = msg
            window.event.returnValue = msg
            return msg
        }
    })
}


/* DECK EDITING */

function addNewCard() {
    let template = document.createElement('template')
    template.innerHTML = cardTemplate.trim()
    
    document.getElementById('container').appendChild(template.content.firstChild)
    updateButtons()
}

function updateButtons() {
    updateSaveButton()
    updateDeleteButtons()
    updateFormattingButtons()
    updateColorPickers()
    updateImageButtons('term')
    updateImageButtons('definition')

    document.getElementById('new-card').onclick = addNewCard
}

function updateSaveButton() {
    // cannot save until user typed in deck's name
    const deckName = document.getElementById('name')
    const saveBtn = document.getElementById('save-btn')

    deckName.addEventListener('keyup', () => {
        saveBtn.disabled = (deckName.value === '')
    })

    saveBtn.onclick = save
}

function updateDeleteButtons() {
    document.getElementsByName('delete-btn').forEach(btn => {
        btn.onclick = () => {
            const card = btn.parentElement
            btn.parentElement.parentElement.removeChild(card)
        }
    })
}

function updateFormattingButtons() {
    document.getElementsByName('tool').forEach(tool => {
        tool.addEventListener('click', () => {
            document.execCommand(tool.dataset['command'], false, null)            
            getEditor(tool).focus()
        })
    })
}

function updateColorPickers() {
    document.getElementsByName('picker').forEach(picker => {
        picker.addEventListener('change', () => {
            document.execCommand('styleWithCSS', false,  true)
            document.execCommand('foreColor', false, picker.value)
            getEditor(picker).focus()
        })
    })
}

function getEditor(child) {
    const getSiblings = (node) => {
        return Array.from(node.parentElement.childNodes)
            .filter(element => element.nodeType === Node.ELEMENT_NODE)  // filter out text nodes
    }

    const getEditor = (node) => {
        let siblings = getSiblings(node)
        let editors = siblings.filter(element => {
            let name = element.getAttribute('name')
            return name == 'term' || name == 'definition'
        })

        return (editors.length != 0) ? editors[0] : getEditor(node.parentElement)
    }
    
    return getEditor(child)
}

function updateImageButtons(type) {
    const imageName = type + '-image'
    const previewName = type + '-preview'
    const deleteBtnName = 'del-' + type + '-img'

    hideAndShowImageControls(imageName, previewName, deleteBtnName)

    // image upload
    document.getElementsByName(imageName).forEach(input => {
        input.onchange = () => {
            if(input.files) {
                // get corresponging image preview node
                const img = Array.from(input.parentElement.childNodes).filter(element => element.name == previewName)[0]
                img.src = URL.createObjectURL(input.files[0])
            }
            hideAndShowImageControls(imageName, previewName, deleteBtnName)
        }
    })

    // image delete
    document.getElementsByName(deleteBtnName).forEach(btn => {
        btn.onclick = () => {
            // get corresponding image input and preview
            const file = Array.from(btn.parentElement.childNodes).filter(element => element.name == imageName)[0]
            const preview = Array.from(btn.parentElement.childNodes).filter(element => element.name == previewName)[0]
            file.value = ''
            preview.src = ''
            hideAndShowImageControls(imageName, previewName, deleteBtnName)
        }
    })
}

function hideAndShowImageControls(imageName, previewName, deleteBtnName) {
    let imageInputs = Array.from(document.getElementsByName(imageName))
    let imagePreviews = Array.from(document.getElementsByName(previewName))
    let deleteBtns = Array.from(document.getElementsByName(deleteBtnName))

    const imageFormattingControls = imagePreviews.map((preview, index) => {
        // zip file upload, image preview nodes and image delete buttons
        return {
            'input': imageInputs[index],
            'controls': {
                'preview': preview,
                'delete': deleteBtns[index]
            }
        }
    })

    // enable/disable preview and delete button depending on choosen image
    imageFormattingControls.forEach(pair => {
        let visibility = (pair.controls.preview.getAttribute('src') === '') ? 'hidden' : 'visible'
        Object.values(pair.controls).forEach(element => element.style.visibility = visibility)

        // invert visibility for input
        pair.input.style.visibility = (visibility == 'hidden') ? 'visible' : 'hidden'
    })
}


/* SAVE AND LOAD */

function save() {
    warn = false

    // disable color pickers so they are not sent with POST
    Array.from(document.getElementsByTagName('input'))
        .filter(element => element.getAttribute('type') == 'color')
        .forEach(input => input.removeAttribute('name'))

    // are we editing an existing deck?
    let update = (document.getElementsByName('update').length !== 0)

    // initialize deck data
    const deck = document.createElement('input')
    deck.setAttribute('type', 'hidden')
    deck.setAttribute('name', 'deck')
    deck.setAttribute('value', getDeckJson(update))
    
    const form = document.getElementById('editor')
    form.appendChild(deck)
    form.submit()
}

/** @param {boolean} addPrimaryKey - used when editing an existing deck */
function getDeckJson(addPrimaryKey) {
    const deck = {
        'name': document.getElementById('name').value,
        'description': document.getElementById('description').value,
        'uuid': document.getElementById('uuid').value,
        'cards': []
    }

    document.getElementsByName('card').forEach(element => {
        const card = {
            'term': getText(element, 'term'),
            'term_image': getImage(element, 'term'),
            'definition': getText(element, 'definition'),
            'definition_image': getImage(element, 'definition')
        }
        deck.cards.push(card)
    })

    if(addPrimaryKey) {
        const ids = Array.from(document.getElementsByName('card')).map(card => card.getAttribute('id'))
        for(let i = 0; i < deck.cards.length; i++) {
            deck.cards[i].pk = parseInt(ids[i])
        }
    }

    return JSON.stringify(deck)
}

function getText(node, type) {
    const text = Array.from(node.getElementsByTagName('div')).filter(div => div.getAttribute('name') == type)[0]
    return text.innerHTML
}

function getImage(node, type) {
    const inputName = type + '-image'
    const previewName = type + '-preview'

    // check input tag in case a new image has been uploaded
    let image = Array.from(node.getElementsByTagName('input')).filter(input => input.getAttribute('name') == inputName)[0]
    if(image.value !== '') {
        return getFilename(image.value)
    }

    // check preview img tag in case of preloaded images (used when editing an existing deck)
    image = Array.from(node.getElementsByTagName('img')).filter(img => img.getAttribute('name') == previewName)[0]
    return getFilename(image.getAttribute('src'))
}

function load(deck, cards) {
    document.getElementById('save-btn').disabled = false

    // fill in deck data
    document.getElementById('name').value = deck.fields.name
    document.getElementById('description').value = deck.fields.description

    // fill in cards data
    let terms = Array.from(document.getElementsByName('term'))
    let definitions = Array.from(document.getElementsByName('definition'))

    // fill in image data
    let term_previews = Array.from(document.getElementsByName('term-preview'))
    let definition_previews = Array.from(document.getElementsByName('definition-preview'))

    for(let i = 0; i < terms.length; i++) {
        terms[i].innerHTML = cards[i].fields.term
        term_previews[i].src = loadImage(cards[i].fields.term_image)
    
        definitions[i].innerHTML = cards[i].fields.definition
        definition_previews[i].src = loadImage(cards[i].fields.definition_image)
    }

    addUpdateFlag()
    assignIds()
}

function loadImage(src) {
    const MEDIA_ROOT = '/static/media/'
    return (src === '') ? src : window.location.origin + MEDIA_ROOT + src
}

/** Adds an update input tag so the server can resolve the POST accordingly */
function addUpdateFlag() {
    const input = document.createElement('input')
    input.setAttribute('type', 'hidden')
    input.setAttribute('name', 'update')
    input.setAttribute('value', true)
    document.getElementById('editor').appendChild(input)
}

/** Assigns ids to the cards from the database */
function assignIds() {
    const ids = JSON.parse(rawCards)
    let cards = document.getElementsByName('card')
    
    for(let i = 0; i < cards.length; i++) {
        cards[i].setAttribute('id', ids[i].pk)
    }
}

function getFilename(path) {
    let startIndex = (path.indexOf('\\') >= 0 ? path.lastIndexOf('\\') : path.lastIndexOf('/'))
    let filename = path.substring(startIndex)
    if(filename.indexOf('\\') === 0 || filename.indexOf('/') === 0) {
        filename = filename.substring(1)
    }
    return filename
}