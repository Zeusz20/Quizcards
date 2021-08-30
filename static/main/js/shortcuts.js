/** Helper class, that offers a short form of commonly used verbose functionalities. */
class Shortcuts {

    getCSRFToken() {
        return document.getElementsByName('csrfmiddlewaretoken')[0].value
    }

    getElementsByLabel(label) {
        return document.querySelectorAll(`[data-label=${label}]`)
    }

    getAllChildNodes(parent) {
        let children = []

        Array.from(parent.childNodes)
            .filter(child => child.nodeType == Node.ELEMENT_NODE)
            .forEach(child => {
                children.push(child)
                children = children.concat(this.getAllChildNodes(child))
        })

        return children
    }

    /** Uses the display property hide elements. (display: none;) */
    hideElement(element) {
        element.classList.add('hidden')
    }

    showElement(element) { 
        element.classList.remove('hidden')
    }

    urlCopy() {
        const textToCopy = document.getElementById('copy')
        textToCopy.select()
        navigator.clipboard.writeText(textToCopy.value)
    }

}

// Shortcut class instansnce to access shortcut functions
const shortcuts = new Shortcuts()