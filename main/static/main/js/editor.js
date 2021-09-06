var warn = true
var saveButtonListener = null

init()


function init() {
    window.onload = warnUser
    document.getElementById('new-card-btn').onclick = addNewCard
    document.getElementById('save-btn').onclick = save
    saveButtonListener = setInterval(canSave, 100)
    initEditor()
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

function initTinyMCE() {
    tinymce.init(getTinyMCEConfig('term'))
    tinymce.init(getTinyMCEConfig('definition'))
}

function getTinyMCEConfig(type) {
    return {
        selector: `div[data-label="${type}"]`,
        menubar: false,
        plugins: 'textcolor',
        toolbar: 'undo redo | bold italic underline | forecolor backcolor',
        statusbar: false,
    }
}

function initEditor() {
    initTinyMCE()
    initDeleteButton()
    initImageButtons('term')
    initImageButtons('definition')
}

/* DECK EDITING */

function addNewCard() {        
    const raw = document.getElementById('template').cloneNode(true)
    const template = document.createElement('template')
    template.innerHTML = raw.innerHTML.trim()

    // add data-label attribute now, so it doesn't count towards total card count
    template.content.firstChild.setAttribute('data-label', 'card')

    // replace id attributes of the card faces with data-label attribute, so tinyMCE can instantiate the editors correctly
    shortcuts.getAllChildNodes(template.content.firstChild)
        .filter(element => {
            let id = element.getAttribute('id')
            return id == 'term' || id == 'definition'
        })
        .forEach(element => {
            let value = element.getAttribute('id')
            element.removeAttribute('id')
            element.setAttribute('data-label', value)
        })

    document.getElementById('container').appendChild(template.content.firstChild)

    initEditor()
}

function initDeleteButton() {
    document.getElementsByName('delete-btn').forEach(btn => {
        if(btn.onclick == null) {
            btn.onclick = () => {
                getCard(btn).remove()
            }
        }
    })
}

function getCard(child) {
    if(child.parentElement.getAttribute('data-label') == 'card') {
        return child.parentElement
    }
    
    return getCard(child.parentElement)
}

function getEditors(parent, acc=[]) {
    parent.childNodes.forEach(child => {
        if(child.nodeType == Node.ELEMENT_NODE) {
            let name = child.getAttribute('data-label')
            if(name == 'term' || name == 'definition') {
                acc.push(child)
            }
            else {
                getEditors(child, acc)
            }
        }
    })
    
    return acc.map(editor => editor.id)
}

function initImageButtons(type) {
    const imageName = type + '-image'
    const previewName = type + '-preview'
    const deleteBtnName = 'del-' + type + '-img'

    hideOrShowImageControls(imageName, previewName, deleteBtnName)

    // image upload
    document.getElementsByName(imageName).forEach(input => {
        if(input.onchange == null) {
            input.onchange = () => {
                if(input.files) {
                    // get corresponging image preview node
                    const img = Array.from(input.parentElement.childNodes).filter(element => element.name == previewName)[0]
                    img.src = URL.createObjectURL(input.files[0])
                }
                hideOrShowImageControls(imageName, previewName, deleteBtnName)
            }
        }
    })

    // image delete
    document.getElementsByName(deleteBtnName).forEach(btn => {
        if(btn.onclick == null) {
            btn.onclick = () => {
                // get corresponding image input and preview
                const file = Array.from(btn.parentElement.childNodes).filter(element => element.name == imageName)[0]
                const preview = Array.from(btn.parentElement.childNodes).filter(element => element.name == previewName)[0]
                file.value = ''
                preview.src = ''
                hideOrShowImageControls(imageName, previewName, deleteBtnName)
            }
        }
    })
}

function hideOrShowImageControls(imageName, previewName, deleteBtnName) {
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

    // enable/disable preview and delete button, depending on if image exists
    imageFormattingControls.forEach(formatting => {
        let imageExists = (formatting.controls.preview.getAttribute('src') !== '')

        Object.values(formatting.controls).forEach(ctrl => {
            // hide/show the formatting controls (image preview and delete button)
            if(imageExists) {
                shortcuts.showElement(ctrl)
            }
            else {
                shortcuts.hideElement(ctrl)
            }
        })

        // invert visibility for image input
        if(imageExists) {
            shortcuts.hideElement(formatting.input)
        }
        else {
            shortcuts.showElement(formatting.input)
        }
    })
}


/* SAVE */

/* save button event listener */
function canSave() {
    const button = document.getElementById('save-btn')
    const name = document.getElementById('name').value.trim()
    const cards = shortcuts.getElementsByLabel('card').length
    
    // deck must have a name and a minimum of 2 cards
    button.disabled = (name === '' || cards < 2)
}

function save() {
    warn = false
    clearInterval(saveButtonListener)

    // checks for an update flag (are we editing an existing deck)
    let update = (document.getElementById('uuid').value !== '')

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

    // save contents to selector
    tinymce.triggerSave()

    shortcuts.getElementsByLabel('card').forEach(element => {
        const card = {
            'term': getText(element, 'term'),
            'term_image': getImage(element, 'term'),
            'definition': getText(element, 'definition'),
            'definition_image': getImage(element, 'definition')
        }
        deck.cards.push(card)
    })

    if(addPrimaryKey) {
        const ids = Array.from(shortcuts.getElementsByLabel('card')).map(card => card.getAttribute('id'))
        for(let i = 0; i < deck.cards.length; i++) {
            deck.cards[i].pk = parseInt(ids[i])
        }
    }

    return JSON.stringify(deck)
}

function getText(node, type) {
    const text = Array.from(shortcuts.getAllChildNodes(node)).filter(child => child.getAttribute('data-label') == type)[0]
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

function getFilename(path) {
    // {~/path/to/file/}filename.ext - everything in {} is replaced
    return path.replace(/.*(\/|\\)/g, '')
}
