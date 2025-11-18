const currentTheme = localStorage.getItem('theme') ? localStorage.getItem('theme') : null;

if (currentTheme) {
    document.documentElement.setAttribute('data-theme', currentTheme);

    if (currentTheme === 'pink') {
        toggleSwitch.checked = true;
    }
}

const toggleSwitch = document.querySelector('.theme-switch input[type="checkbox"]');

function switchTheme(e) {
    if (e.target.checked) {
        document.documentElement.setAttribute('data-theme', 'pink');
        localStorage.setItem('theme', 'pink'); //this will be set to dark
    }
    else {
        document.documentElement.setAttribute('data-theme', 'purple');
        localStorage.setItem('theme', 'purple'); //this will be set to light
    }
}

toggleSwitch.addEventListener('change', switchTheme, false);