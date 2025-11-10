document.addEventListener('DOMContentLoaded', () => {
    // Find all tabbed code blocks on the page
    const tabbedCodeBlocks = document.querySelectorAll('.code-tabs');

    tabbedCodeBlocks.forEach(block => {
        const contentWrapper = block.querySelector('.content');
        if (!contentWrapper) return;

        // Find all the code blocks *directly* under the .content
        const codeBlocks = Array.from(contentWrapper.querySelectorAll(':scope > .listingblock'));
        
        // If there are no listing blocks, do nothing.
        if (codeBlocks.length === 0) return;

        // Create the navigation container
        const tabNav = document.createElement('div');
        tabNav.className = 'tab-nav';

        const tabPanels = []; // This will just be the codeBlocks

        codeBlocks.forEach((codeBlock, index) => {
            // Find the title *inside* this specific code block
            const titleElement = codeBlock.querySelector(':scope > .title');
            const titleText = titleElement ? titleElement.textContent : `Tab ${index + 1}`;

            // IMPORTANT: Remove the original title element
            // so it doesn't appear above the code block.
            if (titleElement) {
                titleElement.remove();
            }

            // Create the tab button
            const tabButton = document.createElement('button');
            tabButton.className = 'tab-link';
            tabButton.textContent = titleText;
            
            // Store the code block this tab corresponds to
            tabPanels.push(codeBlock);

            // Add click event
            tabButton.addEventListener('click', () => {
                // Deactivate all tabs and panels in this group
                tabNav.querySelectorAll('.tab-link').forEach(btn => btn.classList.remove('active'));
                tabPanels.forEach(panel => panel.classList.remove('active'));

                // Activate the clicked tab and its corresponding panel
                tabButton.classList.add('active');
                codeBlock.classList.add('active');
            });

            tabNav.appendChild(tabButton);
        });

        // Add the new tab navigation to the top of the block's content
        contentWrapper.prepend(tabNav);

        // Activate the first tab by default
        if (tabNav.children.length > 0) {
            tabNav.children[0].classList.add('active');
        }
        if (tabPanels.length > 0) {
            tabPanels[0].classList.add('active');
        }
    });
});
