document.addEventListener('DOMContentLoaded', () => {
    // 新增封面與主畫面切換
    const coverScreen = document.getElementById('cover-screen');
    const startButtonImg = document.getElementById('start-button-img');
    const gameWrapper = document.getElementById('game-wrapper');

    // 如果 coverScreen 或 gameWrapper 其中一個不存在，直接 return，避免報錯
    if (!coverScreen || !gameWrapper) return;

    const dialogueArea = document.getElementById('dialogue-area');
    const characterNameDisplay = document.getElementById('character-name');
    const characterBackgroundDisplay = document.getElementById('character-background-summary');
    const replyButtonImg = document.getElementById('reply-button-img');
    const optionBtns = document.querySelectorAll('.option-btn');
    const characterAvatarImg = document.getElementById('character-avatar');
    const comboAvatarImg = document.getElementById('combo-avatar-img');

    let currentGame = {
        characterName: null,
        selectedOptionIndex: null,
        correctStreak: 0
    };

    const openingMusic = document.getElementById('opening-music');
    const startButtonAudio = document.getElementById('start-button-audio');
    const gameMusic = document.getElementById('game-music');

    const musicTip = document.getElementById('music-tip');

    const comboIntroGif = document.getElementById('combo-intro-gif');

    // 嘗試自動播放開場音樂，僅在封面顯示時
    function tryPlayOpeningMusic() {
        if (openingMusic && openingMusic.paused && coverScreen.style.display !== 'none') {
            openingMusic.volume = 0.18;
            openingMusic.play().catch(() => {});
        }
    }
    document.addEventListener('DOMContentLoaded', tryPlayOpeningMusic);
    document.body.addEventListener('click', tryPlayOpeningMusic, { once: true });

    // 預設只顯示封面，隱藏遊戲主介面
    if (gameWrapper) gameWrapper.style.display = 'none';
    if (coverScreen) coverScreen.style.display = 'flex';

    function showLoading() {
        document.getElementById('loading-overlay').style.display = 'flex';
    }
    function hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
    }

    startButtonImg.addEventListener('click', () => {
        showLoading();
        // 播放開始鍵音效（音量最大）
        if (startButtonAudio) {
            startButtonAudio.currentTime = 0;
            startButtonAudio.volume = 1;
            startButtonAudio.play();
        }
        // 進入遊戲時暫停開場音樂
        if (openingMusic) {
            openingMusic.pause();
            openingMusic.currentTime = 0;
        }
        // 播放遊戲內音樂
        if (gameMusic) {
            gameMusic.volume = 0.22;
            gameMusic.currentTime = 0;
            gameMusic.play().catch(() => {});
        }
        coverScreen.style.display = 'none';
        gameWrapper.style.display = 'flex';
        startGame();
    });

    // 選項點擊效果
    optionBtns.forEach((btn, idx) => {
        btn.addEventListener('click', () => {
            optionBtns.forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            currentGame.selectedOptionIndex = idx;
        });
    });

    // 回覆按鈕觸發送出
    replyButtonImg.addEventListener('click', submitAnswer);

    // 痛扁環節控制
    const comboOverlay = document.getElementById('combo-overlay');
    const comboAvatar = comboOverlay ? comboOverlay.querySelector('.combo-avatar') : null;

    function showComboOverlay(onComboEnd) {
        // 防止重複觸發
        if (comboOverlay.dataset.active === '1' || comboIntroGif.dataset.active === '1') return;
        // 先顯示 combo-intro-gif
        if (comboIntroGif) {
            comboIntroGif.style.display = 'block';
            comboIntroGif.dataset.active = '1';
            setTimeout(() => {
                comboIntroGif.style.display = 'none';
                comboIntroGif.dataset.active = '0';
                // 再顯示 combo-overlay
                comboOverlay.style.display = 'flex';
                comboOverlay.dataset.active = '1';
                let comboActive = true;
                // combo 頭貼切換
                if (comboAvatarImg) {
                    comboAvatarImg.src = '/static/images/combo_normal.png';
                    comboAvatarImg.onmousedown = function() {
                        if (!comboActive) return;
                        comboAvatarImg.src = '/static/images/combo_hit.png';
                        comboAvatarImg.classList.remove('combo-hit');
                        void comboAvatarImg.offsetWidth;
                        comboAvatarImg.classList.add('combo-hit');
                        window.addEventListener('mouseup', handleComboMouseUp);
                    };
                    comboAvatarImg.onmouseleave = function() {
                        if (!comboActive) return;
                        comboAvatarImg.src = '/static/images/combo_normal.png';
                    };
                    function handleComboMouseUp() {
                        if (!comboActive) return;
                        comboAvatarImg.src = '/static/images/combo_normal.png';
                        window.removeEventListener('mouseup', handleComboMouseUp);
                    }
                }
                // 監聽 combo 特效
                function handleComboClick(e) {
                    // 播放 combo 音效
                    const comboSound = document.getElementById('combo-sound');
                    if (comboSound) {
                        comboSound.currentTime = 0;
                        comboSound.play();
                    }
                    const effectImgs = [
                        '/static/images/combo_effect1.png',
                        '/static/images/combo_effect2.png'
                    ];
                    const img = document.createElement('img');
                    img.src = effectImgs[Math.floor(Math.random() * effectImgs.length)];
                    img.style.position = 'fixed';
                    img.style.left = e.clientX - 100 + 'px';
                    img.style.top = e.clientY - 100 + 'px';
                    img.style.maxWidth = '200px';
                    img.style.maxHeight = '200px';
                    img.style.objectFit = 'contain';
                    img.style.pointerEvents = 'none';
                    img.style.zIndex = 10000;
                    img.style.transition = 'opacity 0.4s';
                    document.body.appendChild(img);
                    setTimeout(() => {
                        img.style.opacity = 0;
                        setTimeout(() => img.remove(), 400);
                    }, 500);
                    // 讓 combo 頭貼也搖晃
                    if (comboAvatarImg) {
                        comboAvatarImg.classList.remove('combo-hit');
                        void comboAvatarImg.offsetWidth;
                        comboAvatarImg.classList.add('combo-hit');
                    }
                }
                comboOverlay.addEventListener('click', handleComboClick);
                // 5秒後自動結束
                setTimeout(() => {
                    comboActive = false;
                    comboOverlay.style.display = 'none';
                    comboOverlay.dataset.active = '0';
                    comboOverlay.removeEventListener('click', handleComboClick);
                    // 移除所有 combo 特效圖片
                    document.querySelectorAll('.combo-effect-img').forEach(el => el.remove());
                    if (typeof onComboEnd === 'function') onComboEnd();
                }, 5000);
            }, 2000); // GIF 顯示 2 秒
            return;
        }
        // 若找不到 GIF，直接顯示 combo-overlay
        comboOverlay.style.display = 'flex';
        comboOverlay.dataset.active = '1';
        let comboActive = true;
        // combo 頭貼切換
        if (comboAvatarImg) {
            comboAvatarImg.src = '/static/images/combo_normal.png';
            comboAvatarImg.onmousedown = function() {
                if (!comboActive) return;
                comboAvatarImg.src = '/static/images/combo_hit.png';
                comboAvatarImg.classList.remove('combo-hit');
                void comboAvatarImg.offsetWidth;
                comboAvatarImg.classList.add('combo-hit');
                window.addEventListener('mouseup', handleComboMouseUp);
            };
            comboAvatarImg.onmouseleave = function() {
                if (!comboActive) return;
                comboAvatarImg.src = '/static/images/combo_normal.png';
            };
            function handleComboMouseUp() {
                if (!comboActive) return;
                comboAvatarImg.src = '/static/images/combo_normal.png';
                window.removeEventListener('mouseup', handleComboMouseUp);
            }
        }
        function handleComboClick(e) {
            // 播放 combo 音效
            const comboSound = document.getElementById('combo-sound');
            if (comboSound) {
                comboSound.currentTime = 0;
                comboSound.play();
            }
            const effectImgs = [
                '/static/images/combo_effect1.png',
                '/static/images/combo_effect2.png'
            ];
            const img = document.createElement('img');
            img.src = effectImgs[Math.floor(Math.random() * effectImgs.length)];
            img.style.position = 'fixed';
            img.style.left = e.clientX - 100 + 'px';
            img.style.top = e.clientY - 100 + 'px';
            img.style.maxWidth = '200px';
            img.style.maxHeight = '200px';
            img.style.objectFit = 'contain';
            img.style.pointerEvents = 'none';
            img.style.zIndex = 10000;
            img.style.transition = 'opacity 0.4s';
            document.body.appendChild(img);
            setTimeout(() => {
                img.style.opacity = 0;
                setTimeout(() => img.remove(), 400);
            }, 500);
            // 讓 combo 頭貼也搖晃
            if (comboAvatarImg) {
                comboAvatarImg.classList.remove('combo-hit');
                void comboAvatarImg.offsetWidth;
                comboAvatarImg.classList.add('combo-hit');
            }
        }
        comboOverlay.addEventListener('click', handleComboClick);
        setTimeout(() => {
            comboActive = false;
            comboOverlay.style.display = 'none';
            comboOverlay.dataset.active = '0';
            comboOverlay.removeEventListener('click', handleComboClick);
            document.querySelectorAll('.combo-effect-img').forEach(el => el.remove());
            if (typeof onComboEnd === 'function') onComboEnd();
        }, 5000);
    }

    function startGame() {
        fetch('/start_game', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                if (data.error) {
                    dialogueArea.textContent = data.error + (data.details ? ` (${data.details})` : '');
                    return;
                }
                updateGameUI(data);
                currentGame.correctStreak = 0;
            })
            .catch(error => {
                hideLoading();
                dialogueArea.textContent = '開始遊戲失敗：' + error.message;
            });
    }

    function updateGameUI(data, showOptions = true) {
        currentGame.characterName = data.character_name;
        characterNameDisplay.textContent = data.character_name;
        characterBackgroundDisplay.textContent = data.background_summary || '';
        dialogueArea.textContent = data.opening_dialogue;
        // 設定角色頭貼
        if (characterAvatarImg && data.avatar) {
            characterAvatarImg.src = '/static/images/' + data.avatar;
        }
        dialogueArea.classList.remove('long-text');
        // 更新三個選項
        const btns = document.querySelectorAll('.option-btn');
        btns.forEach((btn, idx) => {
            btn.textContent = data.options[idx] || '';
            btn.classList.remove('selected');
            btn.classList.remove('long-text');
            btn.style.display = showOptions ? '' : 'none';
            btn.onclick = () => {
                btns.forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                currentGame.selectedOptionIndex = idx;
            };
        });
        // 控制回覆按鈕顯示
        if (replyButtonImg) replyButtonImg.style.display = showOptions ? '' : 'none';
        currentGame.selectedOptionIndex = null;
        hideLoading();
    }

    function submitAnswer() {
        if (currentGame.selectedOptionIndex === null) {
            dialogueArea.textContent = '請先選擇一個回覆！';
            return;
        }
        dialogueArea.textContent = '回覆中...';
        fetch('/submit_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ option_index: currentGame.selectedOptionIndex })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                dialogueArea.textContent = data.error + (data.details ? ` (${data.details})` : '');
                return;
            }
            // 痛扁三次，先顯示正常回應，再顯示被痛扁回覆，最後進入痛扁動畫，動畫結束後自動切換角色
            if (data.action === 'final_combo') {
                // 只顯示一次角色回覆
                dialogueArea.textContent = data.normal_reply;
                setTimeout(() => {
                    // 直接進入痛扁動畫，動畫結束後自動loading並切換角色
                    showComboOverlay(() => {
                        showLoading();
                        fetch('/next_character', { method: 'POST' })
                            .then(resp => resp.json())
                            .then(newChar => {
                                updateGameUI(newChar, true);
                            })
                            .catch(err => {
                                hideLoading();
                                dialogueArea.textContent = '切換角色失敗：' + err.message;
                            });
                    });
                }, 1200);
                return;
            }
            // 痛扁（combo）流程維持原本動畫
            if (data.action === 'combo') {
                dialogueArea.textContent = data.opening_dialogue;
                dialogueArea.classList.add('combo-effect');
                setTimeout(() => {
                    dialogueArea.classList.remove('combo-effect');
                    showComboOverlay(() => {
                        // 角色回應後自動延遲顯示選項
                        setTimeout(() => {
                            updateGameUI(data, true);
                        }, 1200);
                    });
                }, 500);
                return;
            }
            // 一般回合：只顯示角色回應，延遲自動顯示選項
            dialogueArea.textContent = data.opening_dialogue;
            updateGameUI(data, false);
            setTimeout(() => {
                updateGameUI(data, true);
            }, 1200);
        })
        .catch(error => {
            dialogueArea.textContent = '提交回答失敗：' + error.message;
        });
        document.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
    }

    // 讓滑鼠在畫面上移動即可觸發音樂播放，並自動隱藏提示
    function handleMouseMove() {
        tryPlayOpeningMusic();
        if (musicTip) musicTip.style.display = 'none';
        window.removeEventListener('mousemove', handleMouseMove);
    }
    window.addEventListener('mousemove', handleMouseMove);
}); 