document.addEventListener('DOMContentLoaded', () => {
  const panels = document.querySelectorAll('.panel');
  let highestZIndex = 1; 

  panels.forEach(panel => {
    let currentX = 0, currentY = 0, initialX = 0, initialY = 0;
    let xOffset = 0, yOffset = 0;

    panel.addEventListener('pointerdown', function(e) {
      // Prevent parent panels from also catching this drag event
      e.stopPropagation();

      // Prevent browser native drag conflicts
      e.preventDefault();

      // Bring to front
      highestZIndex++;
      panel.style.zIndex = highestZIndex;
      panel.style.userSelect = 'none'; // Avoid text selection while dragging

      initialX = e.clientX - xOffset;
      initialY = e.clientY - yOffset;

      document.addEventListener('pointerup', closeDragElement);
      document.addEventListener('pointermove', elementDrag, { passive: false });
    }, { passive: false });

    function elementDrag(e) {
      e.preventDefault(); 
      currentX = e.clientX - initialX;
      currentY = e.clientY - initialY;
      xOffset = currentX;
      yOffset = currentY;

      // Moves the panel visually without removing its physical footprint from your grid
      panel.style.transform = `translate(${currentX}px, ${currentY}px)`;
    }

    function closeDragElement() {
      panel.style.userSelect = '';
      document.removeEventListener('pointerup', closeDragElement);
      document.removeEventListener('pointermove', elementDrag);
    }
  });
});