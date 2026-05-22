
// ==========================================
// 1. INITIALIZATION & SETUP
// ==========================================

// Injects the YouTube IFrame API script into your page
function onYouTubeIframeAPIReady() {
  const widgets = findAudioWidgets(); // Assuming this returns your .yt-player elements

  widgets.forEach((widget) => {
    // 1. Read the data tags
    const mediaId = widget.getAttribute('data-id');
    const mediaType = widget.getAttribute('data-type');
    const isPlaylist = mediaType === "playlist"; // Simple boolean to make checks easier

    console.log("Preparing to load a", mediaType, "with ID:", mediaId);

    // 2. Inject ONLY the inner HTML using template literals
    // Notice how we group the new .prev-btn and .next-btn with the .play-btn CSS
    // and use ${isPlaylist ? ... : ''} to only render them when needed!
    widget.innerHTML = `
      <style>
        /* Base player container */
        .yt-player {
          width: 100%;
          max-width: 800px;
          background-color: var(--panel-bg);
          box-sizing: border-box;
          position: relative;
        }
        
        .yt-player iframe {
          position: absolute;
          width: 0px;
          height: 0px;
          opacity: 0;
          pointer-events: none;
        }

        /* The visible UI wrapper */
        .controls {
          display: flex;
          gap: 8px;
          background-color: var(--panel-bg);
        }

        /* Shared Button Styles */
        .play-btn, .prev-btn, .next-btn {
          width: 44px;
          height: 44px;
          background-color: transparent;
          border: 1px solid var(--panel-border);
          color: var(--text);
          font-size: 16px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          transition: background-color 0.2s ease;
        }

        .play-btn:hover, .prev-btn:hover, .next-btn:hover {
          background-color: var(--bg-shade);
        }

        /* Right Side: Track Info and Progress */
        .track-info-container {
          flex-grow: 1;
          border: 1px solid var(--panel-border);
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          padding: 4px 8px;
          overflow: hidden; 
        }

        /* Top Row of the Right Side */
        .track-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-family: sans-serif;
          font-size: 14px;
          gap: 12px;
        }

        /* MARQUEE SETUP */
        .title-wrapper {
          flex-grow: 1;
          overflow: hidden;
          white-space: nowrap; 
        }

        .track-title {
          display: inline-block;
          color: var(--text);
        }

        .track-title.is-scrolling {
          padding-left: 100%;
          animation: scrollText 12s linear infinite; 
        }

        @keyframes scrollText {
          0% { transform: translateX(0%); }
          100% { transform: translateX(-100%); }
        }

        .time-display {
          color: var(--muted-text);
          white-space: nowrap;
          flex-shrink: 0;
        }

        /* Bottom Row of the Right Side */
        .progress-bar {
          width: 100%;
          margin: 0;
          cursor: pointer;
          accent-color: var(--accent);
        }
      </style>
            
      <div class="yt-embed-target"></div>

      <div class="controls">
        ${isPlaylist ? `<button class="prev-btn">⏮</button>` : ''}
        <button class="play-btn">▶</button>
        ${isPlaylist ? `<button class="next-btn">⏭</button>` : ''}
        
        <div class="track-info-container">
          <div class="track-header">
            <div class="title-wrapper">
              <span class="track-title">Loading track...</span>
            </div>
            <span class="time-display">0:00 / 0:00</span>
          </div>
          <input type="range" class="progress-bar" value="0" min="0" max="100" step="0.1">
        </div>
      </div>
    `;

    // 3. Grab Elements
    const targetElement = widget.querySelector('.yt-embed-target');
    const titleWrapper = widget.querySelector('.title-wrapper');
    const playBtn = widget.querySelector('.play-btn');
    const titleDisplay = widget.querySelector('.track-title');
    const timeDisplay = widget.querySelector('.time-display');
    const progressBar = widget.querySelector('.progress-bar');

    // Only grab these if it's a playlist so we don't get null errors on video players
    const prevBtn = isPlaylist ? widget.querySelector('.prev-btn') : null;
    const nextBtn = isPlaylist ? widget.querySelector('.next-btn') : null;

    let progressTimer;

    // --- The Marquee Checker ---
    const checkMarquee = () => {
      titleDisplay.classList.remove('is-scrolling');
      if (titleDisplay.scrollWidth > titleWrapper.clientWidth) {
        titleDisplay.classList.add('is-scrolling');
      }
    };

    const resizeObserver = new ResizeObserver(() => checkMarquee());
    resizeObserver.observe(titleWrapper);

    // 4. Set up the Configuration Object
    const playerConfig = {
      playerVars: {
        controls: 0,
        disablekb: 1,
        fs: 0,
        playsinline: 1,
        rel: 0,
        iv_load_policy: 3
      },
      events: {
        'onReady': (event) => {
          const videoData = event.target.getVideoData();
          if (videoData && videoData.title) {
            titleDisplay.textContent = videoData.title;
            checkMarquee();
          }
        },
        'onStateChange': (event) => {
          if (event.data === YT.PlayerState.PLAYING) {
            playBtn.textContent = '⏸';

            // PLAYLIST FIX: Update the title when the track changes natively
            const videoData = event.target.getVideoData();
            if (videoData && videoData.title) {
              titleDisplay.textContent = videoData.title;
              checkMarquee();
            }

            progressTimer = setInterval(() => {
              const current = event.target.getCurrentTime();
              const total = event.target.getDuration();
              progressBar.value = (current / total) * 100;
              // Make sure formatTime is defined in your script!
              timeDisplay.textContent = formatTime(current) + ' / ' + formatTime(total);
            }, 500);
          } else {
            playBtn.textContent = '▶';
            clearInterval(progressTimer);
          }
        }
      }
    };

    // 5. Tell YouTube what to load based on the type
    if (isPlaylist) {
      playerConfig.playerVars.listType = 'playlist';
      playerConfig.playerVars.list = mediaId;
    } else {
      playerConfig.videoId = mediaId;
    }

    // Initialize the YouTube Player with the compiled config
    const playerInstance = new YT.Player(targetElement, playerConfig);

    // 6. Wire up the buttons
    playBtn.addEventListener('click', () => {
      const state = playerInstance.getPlayerState();
      if (state === YT.PlayerState.PLAYING) {
        playerInstance.pauseVideo();
      } else {
        playerInstance.playVideo();
      }
    });

    if (isPlaylist) {
      prevBtn.addEventListener('click', () => playerInstance.previousVideo());
      nextBtn.addEventListener('click', () => playerInstance.nextVideo());
    }
  });
}
// Drop this anywhere in your script outside the loop
function formatTime(seconds) {
  if (!seconds) return "0:00";
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  // Adds a leading zero if seconds are less than 10
  return minutes + ":" + (remainingSeconds < 10 ? "0" : "") + remainingSeconds;
}
// Scans the DOM for your custom player containers
function findAudioWidgets() {
    return document.querySelectorAll('.yt-player');
}

// ==========================================
// 2. PLAYER CREATION
// ==========================================

// Checks data attributes to decide if it's loading a single video or a list
function determineMediaType(widgetElement) {}

// Builds the actual YT.Player object inside the hidden target div
function createPlayerInstance(widgetElement, mediaType, mediaId) {}

// ==========================================
// 3. YOUTUBE STATE HANDLERS
// ==========================================

// Fires when a YouTube player finishes building and is ready to accept commands
function onPlayerReady(event) {}

// Fires whenever a video plays, pauses, buffers, or changes tracks
function onPlayerStateChange(event) {}

// ==========================================
// 4. UI & METADATA UPDATES
// ==========================================

// Grabs the title and duration from the YT player and updates your HTML
function updatePlayerMetadata(playerInstance, widgetElement) {}

// Updates the range slider value and time text based on current playback
function updateProgressUI(playerInstance, widgetElement) {}

// Starts the interval timer that calls updateProgressUI() while playing
function startProgressTracking(playerInstance, widgetElement) {}

// Stops the interval timer when paused to save CPU
function stopProgressTracking(timerId) {}

// ==========================================
// 5. USER CONTROLS (BUTTON CLICKS)
// ==========================================

// Toggles between .playVideo() and .pauseVideo()
function handlePlayPauseClick(playerInstance) {}

// Calculates where the user clicked/dragged the slider and calls .seekTo()
function handleSeek(event, playerInstance) {}

// Calls .nextVideo() (only applicable if determineMediaType found a playlist)
function handleNextTrackClick(playerInstance) {}

// Calls .previousVideo() (only applicable if determineMediaType found a playlist)
function handlePreviousTrackClick(playerInstance) {}
onYouTubeIframeAPIReady();