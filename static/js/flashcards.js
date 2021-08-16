init()


function init() {
    document.getElementsByName('card').forEach(card => fillCardFace(card))
    document.getElementsByClassName('carousel-item')[0].classList.add('active')
    bindRotation()
}

function startWith() {
    const start = document.getElementsByName('start-with')[0].value
    return (start === '') ? 'term' : start
}

function getCard(child) {
    return (child.parentElement.getAttribute('name') == 'card') ? child.parentElement : getCard(child.parentElement)
}

function bindRotation() {
    document.getElementsByName('rotate-btn').forEach(button => {
        // TODO: 3d rotation
        Node.prototype.flip = false     // saves rotation for each card

        button.onclick = () => {
            button.flip = !button.flip
            fillCardFace(getCard(button), button.flip)
        }
    })
}

function fillCardFace(card, flip=false) {
    const face = getCardElement(card, 'face')
    const term = getCardElement(card, 'term')
    const definition = getCardElement(card, 'definition')

    if(startWith() == 'term') {
        face.innerHTML = flip ? definition.innerHTML : term.innerHTML
    }
    else {
        face.innerHTML = flip ? term.innerHTML : definition.innerHTML
    }
}

function getCardElement(card, name) {
    return Array.from(card.getElementsByTagName('div')).filter(div => div.getAttribute('name') == name)[0]
}
