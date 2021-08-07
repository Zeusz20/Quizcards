var warn = true

init()


function init() {
    window.onload = warnUser

    initTinyMCE()
    updateEditorButtons()
    document.getElementById('save-btn').onclick = save
    document.getElementById('new-card').onclick = addNewCard
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
        selector: `div[name="${type}"]`,
        menubar: false,
        plugins: 'textcolor',
        toolbar: 'undo redo | bold italic underline | forecolor backcolor',
        statusbar: false,
    }
}

/* DECK EDITING */

function addNewCard() {
    let template = document.createElement('template')
    template.innerHTML = cardTemplate.trim()
    
    document.getElementById('container').appendChild(template.content.firstChild)
    
    initTinyMCE()
    updateEditorButtons()
}

function updateEditorButtons() {
    updateDeleteButtons()
    updateImageButtons('term')
    updateImageButtons('definition')
}

function updateDeleteButtons() {
    document.getElementsByName('delete-btn').forEach(btn => {
        btn.onclick = () => {
            let cards = document.getElementsByName('card').length
            if(cards !== 1) {
                // deck must contain at least one card
                const card = getCard(btn)
                const editors = getEditors(card)
                activeEditors = activeEditors.filter(editor => !editors.includes(editor))
                btn.parentElement.parentElement.removeChild(card)
            }
        }
    })
}

function getCard(child) {
    if(child.parentElement.getAttribute('name') == 'card') {
        return child.parentElement
    }
    
    return getCard(child.parentElement)
}

function getEditors(parent, acc=[]) {
    parent.childNodes.forEach(child => {
        if(child.nodeType == Node.ELEMENT_NODE) {
            let name = child.getAttribute('name')
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

function updateImageButtons(type) {
    const imageName = type + '-image'
    const previewName = type + '-preview'
    const deleteBtnName = 'del-' + type + '-img'

    hideOrShowImageControls(imageName, previewName, deleteBtnName)

    // image upload
    document.getElementsByName(imageName).forEach(input => {
        input.onchange = () => {
            if(input.files) {
                // get corresponging image preview node
                const img = Array.from(input.parentElement.childNodes).filter(element => element.name == previewName)[0]
                img.src = URL.createObjectURL(input.files[0])
            }
            hideOrShowImageControls(imageName, previewName, deleteBtnName)
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
            hideOrShowImageControls(imageName, previewName, deleteBtnName)
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

    // enable/disable preview and delete button depending on choosen image
    imageFormattingControls.forEach(pair => {
        let visibility = (pair.controls.preview.getAttribute('src') === '') ? 'hidden' : 'visible'
        Object.values(pair.controls).forEach(element => element.style.visibility = visibility)

        // invert visibility for input
        pair.input.style.visibility = (visibility == 'hidden') ? 'visible' : 'hidden'
    })
}


/* SAVE */

function save() {
    if(canSave()) {
        warn = false

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
    else {
        alert('A deck must have a name and must contain at least 2 cards!')
        warn = true
    }
}

function canSave() {
    const name = document.getElementById('name').value
    const cards = document.getElementsByName('card').length
    return (name !== '' && cards >= 2)
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

function getFilename(path) {
    let startIndex = (path.indexOf('\\') >= 0 ? path.lastIndexOf('\\') : path.lastIndexOf('/'))
    let filename = path.substring(startIndex)
    if(filename.indexOf('\\') === 0 || filename.indexOf('/') === 0) {
        filename = filename.substring(1)
    }
    return filename
}
