const toggleBurger = () => {
    let burgerIcon = document.getElementById('burger');
    let dropMenu = document.getElementById('teamList');
    burgerIcon.classList.toggle('is-active');
    dropMenu.classList.toggle('is-active');
  };