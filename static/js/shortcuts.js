/** Helper class, that offers a short form of commonly used verbose functionalities. */
class Shortcuts {

    /** Uses the display property hide elements. (display: none;) */
    hideElement(element) {
        element.classList.add('hidden')
    }

    showElement(element) { 
        element.classList.remove('hidden')
    }

    /** Uses bootstrap to hide an element. (uses visibility property) */
    bsHideElement(element) {
        element.classList.add('invisible')
    }

    /** Uses bootstrap to show an element. */
    bsShowElement(element) {
        element.classList.remove('invisible')
    }

}

// Shortcut class instansnce to access shortcut functions
const shortcuts = new Shortcuts()