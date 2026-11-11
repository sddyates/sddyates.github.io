/*
	Highlights the link in the sticky section bar (#nav) for the section
	currently on screen. A section counts as current once its top has
	scrolled past a line 30% down the window. Sections without a nav link
	(e.g. Past Research) keep the previous link highlighted.
*/
(function () {
	var links = Array.prototype.slice.call(document.querySelectorAll('#nav a[href^="#"]'));
	var items = links
		.map(function (link) {
			return { link: link, section: document.getElementById(link.getAttribute('href').slice(1)) };
		})
		.filter(function (item) { return item.section; });

	if (!items.length) return;

	function update() {
		var line = window.innerHeight * 0.3;
		var current = items[0];

		items.forEach(function (item) {
			if (item.section.getBoundingClientRect().top <= line) current = item;
		});

		// At the very bottom of the page, the last section is current even if
		// it is too short to reach the line.
		var doc = document.documentElement;
		if (window.innerHeight + window.pageYOffset >= doc.scrollHeight - 2) {
			current = items[items.length - 1];
		}

		items.forEach(function (item) {
			var active = item === current;
			item.link.classList.toggle('active', active);
			if (active) item.link.setAttribute('aria-current', 'true');
			else item.link.removeAttribute('aria-current');
		});
	}

	// Only a handful of sections are measured, so this is cheap enough to
	// run on every scroll event.
	window.addEventListener('scroll', update, { passive: true });
	window.addEventListener('resize', update);
	window.addEventListener('load', update);
	update();
})();

/*
	Click-to-load 3D model. Each .model-viewer shows a still image and a
	button; the (large) model in data-model is only fetched, in an iframe,
	once the button is clicked.
*/
(function () {
	var viewers = document.querySelectorAll('.model-viewer[data-model]');

	Array.prototype.forEach.call(viewers, function (box) {
		var button = box.querySelector('.model-launch');
		var status = box.querySelector('.model-status');
		if (!button) return;

		button.addEventListener('click', function () {
			var frame = document.createElement('iframe');
			frame.src = box.getAttribute('data-model');
			frame.title = box.getAttribute('data-title') || 'Interactive 3D model';
			frame.setAttribute('allow', 'fullscreen');
			frame.setAttribute('allowfullscreen', '');

			frame.addEventListener('load', function () {
				box.classList.remove('is-loading');
				box.classList.add('is-ready');
				if (status) status.textContent = '';
			});

			button.remove();
			box.classList.add('is-loading');
			if (status) status.textContent = 'Loading 3D model…';
			box.appendChild(frame);
		});
	});
})();
