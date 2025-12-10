/**
 * Farmer Dashboard JavaScript
 * Uses safe DOM methods - no innerHTML with untrusted content
 */

// Check authentication
const accessToken = localStorage.getItem('access_token');
const user = JSON.parse(localStorage.getItem('user') || 'null');

if (!accessToken || !user) {
    window.location.href = '/login';
}

// Check if user is a farmer
if (user && user.role !== 'farmer') {
    window.location.href = '/dashboard';
}

// Store farmer data
let farmerData = null;

// Utility function to safely set text content
function setText(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = text;
}

// Utility function to create element with text
function createEl(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text) el.textContent = text;
    return el;
}

// Load farmer profile
async function loadFarmerProfile() {
    try {
        const response = await fetch('/api/v1/farmers/profile', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
            return;
        }

        if (response.ok) {
            farmerData = await response.json();
            updateSidebar(farmerData);
            updateCompletionBanner(farmerData);
            loadSection('overview');
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

function updateSidebar(data) {
    setText('farm-name', data.farm_name || 'Your Farm');
    setText('user-greeting', 'Hello, ' + data.full_name + '!');

    const status = document.getElementById('profile-status');
    if (data.profile_completed) {
        status.textContent = 'Active';
        status.classList.add('status-active');
    } else {
        status.textContent = 'Setting Up';
        status.classList.add('status-pending');
    }
}

function updateCompletionBanner(data) {
    const banner = document.getElementById('completion-banner');
    if (!data.profile_completed) {
        banner.style.display = 'block';

        let completed = 1;
        if (data.farm_description) completed++;
        if (data.farm_images && data.farm_images.length > 0) completed++;
        if (data.has_bank_account) completed++;

        const progress = (completed / 4) * 100;
        document.getElementById('completion-progress').style.width = progress + '%';
        setText('completion-text', completed + ' of 4 steps completed');
    }
}

// Section navigation
const navItems = document.querySelectorAll('.nav-item[data-section]');
navItems.forEach(item => {
    item.addEventListener('click', function(e) {
        e.preventDefault();
        navItems.forEach(nav => nav.classList.remove('active'));
        this.classList.add('active');
        loadSection(this.dataset.section);
    });
});

function loadSection(section) {
    switch(section) {
        case 'overview':
            renderOverview();
            break;
        case 'farm-details':
            renderFarmDetails();
            break;
        case 'media':
            renderMedia();
            break;
        case 'bank-account':
            renderBankAccount();
            break;
    }
}

function renderOverview() {
    const content = document.getElementById('main-content');
    const template = document.getElementById('overview-template');
    const clone = template.content.cloneNode(true);

    content.textContent = '';
    content.appendChild(clone);

    // Populate stats
    const statsGrid = document.getElementById('stats-grid');
    const stats = [
        { label: 'Products Listed', value: '0', icon: '📦' },
        { label: 'Total Orders', value: '0', icon: '🛒' },
        { label: 'This Month Sales', value: '₹0', icon: '💰' },
        { label: 'Profile Views', value: '0', icon: '👁️' }
    ];

    stats.forEach(stat => {
        const card = createEl('div', 'stat-card');
        card.appendChild(createEl('div', 'stat-icon', stat.icon));
        card.appendChild(createEl('div', 'stat-value', stat.value));
        card.appendChild(createEl('div', 'stat-label', stat.label));
        statsGrid.appendChild(card);
    });

    // Populate actions
    const actionsGrid = document.getElementById('actions-grid');
    const actions = [
        { label: 'Add New Product', href: '/farmer/products/new', icon: '➕' },
        { label: 'View Orders', href: '/farmer/orders', icon: '📋' },
        { label: 'Edit Farm Profile', action: 'farm-details', icon: '✏️' },
        { label: 'Update Photos', action: 'media', icon: '📸' }
    ];

    actions.forEach(action => {
        const btn = document.createElement('a');
        btn.className = 'action-card';
        if (action.href) {
            btn.href = action.href;
        } else {
            btn.href = '#';
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                document.querySelector('[data-section="' + action.action + '"]').click();
            });
        }
        btn.appendChild(createEl('span', 'action-icon', action.icon));
        btn.appendChild(createEl('span', null, action.label));
        actionsGrid.appendChild(btn);
    });
}

function renderFarmDetails() {
    const content = document.getElementById('main-content');
    const template = document.getElementById('farm-details-template');
    const clone = template.content.cloneNode(true);

    content.textContent = '';
    content.appendChild(clone);

    // Populate form values
    if (farmerData) {
        document.getElementById('edit_farm_name').value = farmerData.farm_name || '';
        document.getElementById('farm_description').value = farmerData.farm_description || '';
        document.getElementById('farm_street').value = farmerData.farm_street || '';
        document.getElementById('farm_city').value = farmerData.farm_city || '';
        document.getElementById('farm_state').value = farmerData.farm_state || '';
        document.getElementById('farm_zip').value = farmerData.farm_zip_code || '';

        // Set checkboxes
        if (farmerData.farming_practices) {
            farmerData.farming_practices.forEach(practice => {
                const cb = document.querySelector('input[name="practices"][value="' + practice + '"]');
                if (cb) cb.checked = true;
            });
        }
    }

    // Form submission
    document.getElementById('farm-details-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const practices = Array.from(document.querySelectorAll('input[name="practices"]:checked'))
            .map(cb => cb.value);

        const data = {
            farm_name: document.getElementById('edit_farm_name').value || null,
            farm_description: document.getElementById('farm_description').value || null,
            farm_street: document.getElementById('farm_street').value || null,
            farm_city: document.getElementById('farm_city').value || null,
            farm_state: document.getElementById('farm_state').value || null,
            farm_zip_code: document.getElementById('farm_zip').value || null,
            farming_practices: practices.length > 0 ? practices : null
        };

        try {
            const response = await fetch('/api/v1/farmers/farm', {
                method: 'PUT',
                headers: {
                    'Authorization': 'Bearer ' + accessToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const msgDiv = document.getElementById('form-message');
            if (response.ok) {
                msgDiv.className = 'alert alert-success';
                msgDiv.textContent = 'Farm details updated successfully!';
                msgDiv.style.display = 'block';
                loadFarmerProfile();
            } else {
                const err = await response.json();
                msgDiv.className = 'alert alert-error';
                msgDiv.textContent = err.detail || 'Failed to update';
                msgDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
}

function renderMedia() {
    const content = document.getElementById('main-content');
    const template = document.getElementById('media-template');
    const clone = template.content.cloneNode(true);

    content.textContent = '';
    content.appendChild(clone);

    // Populate images
    const imagesGrid = document.getElementById('images-grid');
    if (farmerData && farmerData.farm_images && farmerData.farm_images.length > 0) {
        farmerData.farm_images.forEach(img => {
            imagesGrid.appendChild(createImageCard(img));
        });
    } else {
        imagesGrid.appendChild(createEl('div', 'empty-state', 'No photos yet. Add photos to showcase your farm!'));
    }

    // Populate videos
    const videosGrid = document.getElementById('videos-grid');
    if (farmerData && farmerData.farm_videos && farmerData.farm_videos.length > 0) {
        farmerData.farm_videos.forEach(vid => {
            videosGrid.appendChild(createVideoCard(vid));
        });
    } else {
        videosGrid.appendChild(createEl('div', 'empty-state', 'No videos yet. Add YouTube or Vimeo videos!'));
    }

    // Button handlers
    document.getElementById('add-image-btn').addEventListener('click', showImageModal);
    document.getElementById('add-video-btn').addEventListener('click', showVideoModal);
}

function createImageCard(img) {
    const card = createEl('div', 'image-card');
    card.dataset.id = img.id;

    const imgEl = document.createElement('img');
    imgEl.src = img.image_url;
    imgEl.alt = img.alt_text || 'Farm image';

    const overlay = createEl('div', 'image-overlay');

    if (img.is_primary) {
        overlay.appendChild(createEl('span', 'primary-badge', 'Primary'));
    }

    const deleteBtn = createEl('button', 'delete-btn', '×');
    deleteBtn.addEventListener('click', () => deleteImage(img.id));
    overlay.appendChild(deleteBtn);

    card.appendChild(imgEl);
    card.appendChild(overlay);

    if (img.caption) {
        card.appendChild(createEl('p', 'image-caption', img.caption));
    }

    return card;
}

function createVideoCard(vid) {
    const card = createEl('div', 'video-card');
    card.dataset.id = vid.id;

    const thumbnail = createEl('div', 'video-thumbnail');
    if (vid.video_platform === 'youtube') {
        thumbnail.style.backgroundImage = 'url(https://img.youtube.com/vi/' + vid.video_id + '/mqdefault.jpg)';
    }

    thumbnail.appendChild(createEl('div', 'play-icon', '▶'));

    const deleteBtn = createEl('button', 'delete-btn', '×');
    deleteBtn.addEventListener('click', () => deleteVideo(vid.id));
    thumbnail.appendChild(deleteBtn);

    card.appendChild(thumbnail);
    card.appendChild(createEl('p', 'video-title', vid.title || 'Farm Video'));

    return card;
}

function renderBankAccount() {
    const content = document.getElementById('main-content');
    const template = document.getElementById('bank-template');
    const clone = template.content.cloneNode(true);

    content.textContent = '';
    content.appendChild(clone);

    // Show current account if exists
    if (farmerData && farmerData.has_bank_account) {
        const accountInfo = document.getElementById('current-account-info');
        const p = createEl('p', 'current-account');
        const strong = createEl('strong', null, 'Current Account: ');
        p.appendChild(strong);
        p.appendChild(document.createTextNode('****' + farmerData.bank_account_last_four));
        accountInfo.appendChild(p);

        document.getElementById('bank-submit-btn').textContent = 'Update Bank Account';
    }

    // Form submission
    document.getElementById('bank-account-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const data = {
            account_holder_name: document.getElementById('account_holder_name').value,
            account_number: document.getElementById('account_number').value,
            routing_number: document.getElementById('routing_number').value,
            bank_name: document.getElementById('bank_name').value || null,
            account_type: document.getElementById('account_type').value
        };

        try {
            const response = await fetch('/api/v1/farmers/bank-account', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + accessToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const msgDiv = document.getElementById('bank-form-message');
            if (response.ok) {
                msgDiv.className = 'alert alert-success';
                msgDiv.textContent = 'Bank account saved successfully!';
                msgDiv.style.display = 'block';
                document.getElementById('bank-account-form').reset();
                loadFarmerProfile();
            } else {
                const err = await response.json();
                msgDiv.className = 'alert alert-error';
                msgDiv.textContent = err.detail || 'Failed to save bank account';
                msgDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
}

// Modal functions
function showImageModal() {
    const template = document.getElementById('image-modal-template');
    const clone = template.content.cloneNode(true);
    document.body.appendChild(clone);

    document.getElementById('close-image-modal').addEventListener('click', () => closeModal('image-modal'));

    document.getElementById('add-image-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const data = {
            image_url: document.getElementById('image_url').value,
            caption: document.getElementById('image_caption').value || null,
            alt_text: document.getElementById('image_alt').value || null,
            is_primary: document.getElementById('image_primary').checked
        };

        try {
            const response = await fetch('/api/v1/farmers/farm/images', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + accessToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                closeModal('image-modal');
                loadFarmerProfile();
                setTimeout(renderMedia, 100);
            } else {
                const err = await response.json();
                const errDiv = document.getElementById('image-modal-error');
                errDiv.textContent = err.detail || 'Failed to add image';
                errDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
}

function showVideoModal() {
    const template = document.getElementById('video-modal-template');
    const clone = template.content.cloneNode(true);
    document.body.appendChild(clone);

    document.getElementById('close-video-modal').addEventListener('click', () => closeModal('video-modal'));

    document.getElementById('add-video-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const data = {
            video_url: document.getElementById('video_url').value,
            title: document.getElementById('video_title').value || null
        };

        try {
            const response = await fetch('/api/v1/farmers/farm/videos', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + accessToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                closeModal('video-modal');
                loadFarmerProfile();
                setTimeout(renderMedia, 100);
            } else {
                const err = await response.json();
                const errDiv = document.getElementById('video-modal-error');
                errDiv.textContent = err.detail || 'Failed to add video';
                errDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.remove();
}

async function deleteImage(id) {
    if (!confirm('Are you sure you want to delete this image?')) return;

    try {
        const response = await fetch('/api/v1/farmers/farm/images/' + id, {
            method: 'DELETE',
            headers: {
                'Authorization': 'Bearer ' + accessToken
            }
        });

        if (response.ok) {
            loadFarmerProfile();
            setTimeout(renderMedia, 100);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function deleteVideo(id) {
    if (!confirm('Are you sure you want to delete this video?')) return;

    try {
        const response = await fetch('/api/v1/farmers/farm/videos/' + id, {
            method: 'DELETE',
            headers: {
                'Authorization': 'Bearer ' + accessToken
            }
        });

        if (response.ok) {
            loadFarmerProfile();
            setTimeout(renderMedia, 100);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Initialize
loadFarmerProfile();
