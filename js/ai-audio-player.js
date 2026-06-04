(function () {
  const players = new WeakMap();
  let apiRequested = false;

  function formatTime(seconds) {
    if (!Number.isFinite(seconds) || seconds <= 0) {
      return "0:00";
    }
    const total = Math.floor(seconds);
    const minutes = Math.floor(total / 60);
    const remainder = String(total % 60).padStart(2, "0");
    return `${minutes}:${remainder}`;
  }

  function setButton(button, isPlaying) {
    button.dataset.state = isPlaying ? "playing" : "paused";
    button.setAttribute("aria-label", isPlaying ? "Pause audio" : "Play audio");
  }

  function setTitle(titleEl, text) {
    const label = text || titleEl.dataset.placeholder || "Loading track";
    titleEl.textContent = label;
    titleEl.classList.toggle("is-marquee", titleEl.scrollWidth > titleEl.clientWidth);
  }

  function updateProgress(state) {
    const duration = state.player.getDuration();
    const current = state.player.getCurrentTime();
    const percent = duration > 0 ? (current / duration) * 100 : 0;
    state.progress.value = String(percent);
    state.progress.style.setProperty("--progress", `${percent}%`);
    state.progressFill.style.width = `${percent}%`;
    state.time.textContent = `${formatTime(current)} / ${formatTime(duration)}`;
  }

  function stopPolling(state) {
    if (state.timer) {
      window.clearInterval(state.timer);
      state.timer = 0;
    }
  }

  function startPolling(state) {
    stopPolling(state);
    updateProgress(state);
    state.timer = window.setInterval(() => updateProgress(state), 300);
  }

  function refreshMetadata(state) {
    const data = state.player.getVideoData ? state.player.getVideoData() : {};
    setTitle(state.title, data && data.title ? data.title : state.fallbackTitle);
  }

  function initPlayer(shell) {
    if (players.has(shell)) {
      return;
    }

    const playlistId = shell.dataset.playlistId || "";
    const videoId = shell.dataset.videoId || "";
    const fallbackTitle = shell.dataset.title || "Loading track";
    const host = shell.querySelector(".indie-audio-youtube");
    const button = shell.querySelector(".indie-audio-toggle");
    const title = shell.querySelector(".indie-audio-title-text");
    const progress = shell.querySelector(".indie-audio-progress");
    const progressFill = shell.querySelector(".indie-audio-progress-fill");
    const time = shell.querySelector(".indie-audio-time");

    if (!host || !button || !title || !progress || !progressFill || !time || !window.YT || !window.YT.Player) {
      return;
    }

    const state = {
      player: null,
      button,
      title,
      progress,
      progressFill,
      time,
      timer: 0,
      fallbackTitle,
    };

    const playerVars = {
      autoplay: 1,
      controls: 0,
      disablekb: 1,
      modestbranding: 1,
      playsinline: 1,
      rel: 0,
    };
    if (playlistId) {
      playerVars.listType = "playlist";
      playerVars.list = playlistId;
    }

    state.player = new window.YT.Player(host, {
      width: "1",
      height: "1",
      videoId,
      playerVars,
      events: {
        onReady() {
          refreshMetadata(state);
          setButton(button, false);
          state.player.playVideo();
          window.setTimeout(() => refreshMetadata(state), 500);
        },
        onStateChange(event) {
          refreshMetadata(state);
          if (event.data === window.YT.PlayerState.PLAYING) {
            setButton(button, true);
            startPolling(state);
            return;
          }
          if (
            event.data === window.YT.PlayerState.PAUSED ||
            event.data === window.YT.PlayerState.ENDED ||
            event.data === window.YT.PlayerState.CUED ||
            event.data === window.YT.PlayerState.UNSTARTED
          ) {
            setButton(button, false);
            stopPolling(state);
            updateProgress(state);
          }
        },
      },
    });

    button.addEventListener("click", () => {
      const currentState = state.player.getPlayerState();
      if (currentState === window.YT.PlayerState.PLAYING) {
        state.player.pauseVideo();
        setButton(button, false);
        return;
      }
      state.player.playVideo();
      setButton(button, true);
    });

    progress.addEventListener("input", () => {
      const duration = state.player.getDuration();
      if (!duration) {
        return;
      }
      const percent = Number(progress.value) / 100;
      state.player.seekTo(duration * percent, true);
      updateProgress(state);
    });

    players.set(shell, state);
  }

  function initAllPlayers() {
    document.querySelectorAll(".indie-audio-player").forEach(initPlayer);
  }

  function requestApi() {
    if (window.YT && window.YT.Player) {
      initAllPlayers();
      return;
    }
    if (apiRequested) {
      return;
    }
    apiRequested = true;
    const previousReady = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = function () {
      if (typeof previousReady === "function") {
        previousReady();
      }
      initAllPlayers();
    };
    const script = document.createElement("script");
    script.src = "https://www.youtube.com/iframe_api";
    document.head.appendChild(script);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", requestApi, { once: true });
  } else {
    requestApi();
  }
})();
