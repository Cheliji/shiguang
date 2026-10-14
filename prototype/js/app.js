/* ============================================
   拾光 · 主应用逻辑
   ============================================ */

(function() {
    'use strict';

    // ===== 状态管理 =====
    const state = {
        currentPage: 'today',
        selectedDate: new Date(),
        todoFilter: 'today',
        goalPeriod: 'week',
        diarySelectedDate: new Date(),
        diaryEditorMode: 'edit',
        editingTask: null,
        archivingTask: null,
        ratingValue: 0,
        selectedRelatedGoals: [],
        tasks: [...MOCK_DATA.tasks],
        archives: [...MOCK_DATA.archives],
        diaries: [...MOCK_DATA.diaries],
        goals: [...MOCK_DATA.goals],
        habits: [...MOCK_DATA.habits],
        heatmapData: MOCK_DATA.heatmapData
    };

    // 工具函数
    const $ = (sel, el = document) => el.querySelector(sel);
    const $$ = (sel, el = document) => Array.from(el.querySelectorAll(sel));
    const fmtDate = (d) => d.toISOString().split('T')[0];
    const fmtDateCN = (d) => `${d.getMonth() + 1}月${d.getDate()}日`;
    const fmtDateShort = (d) => `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    const addDays = (d, n) => { const r = new Date(d); r.setDate(r.getDate() + n); return r; };
    const isSameDay = (a, b) => fmtDate(a) === fmtDate(b);
    const weekdayNames = ['日', '一', '二', '三', '四', '五', '六'];
    const moodEmojis = [
        { threshold: 0, emoji: '😴', text: '今天也是充满希望的一天' },
        { threshold: 0.3, emoji: '☕', text: '慢慢来，一切都在推进中' },
        { threshold: 0.6, emoji: '🙂', text: '进度不错，继续保持' },
        { threshold: 0.99, emoji: '😊', text: ' almost there！再加把劲' },
        { threshold: 1, emoji: '🎉', text: '太棒了！今日任务全部完成' }
    ];

    // ===== InfoBar / Toast =====
    function showInfoBar(message, type = 'success') {
        const container = $('#infobarContainer');
        const bar = document.createElement('div');
        bar.className = `infobar ${type}`;
        bar.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                ${type === 'success'
                    ? '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'
                    : type === 'error'
                    ? '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>'
                    : '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>'}
            </svg>
            <span>${message}</span>
        `;
        container.appendChild(bar);
        setTimeout(() => {
            bar.style.animation = 'infobarFadeOut 300ms forwards';
            setTimeout(() => bar.remove(), 300);
        }, 3000);
    }

    // ===== 导航切换 =====
    function switchPage(page) {
        state.currentPage = page;
        $$('.nav-item').forEach(el => el.classList.toggle('active', el.dataset.page === page));
        $$('.page').forEach(el => el.classList.toggle('active', el.dataset.page === page));
        // 刷新当前页数据
        if (page === 'today') renderTodayPage();
        else if (page === 'todo') renderTodoPage();
        else if (page === 'goal') renderGoalPage();
        else if (page === 'habit') renderHabitPage();
        else if (page === 'diary') renderDiaryPage();
        else if (page === 'stats') renderStatsPage();
    }

    $$('.nav-item').forEach(el => {
        el.addEventListener('click', () => switchPage(el.dataset.page));
    });

    // ===== 日期栏渲染 =====
    function renderDateBar() {
        const container = $('#dateBar');
        const startOfWeek = addDays(state.selectedDate, -state.selectedDate.getDay() + 1); // 周一为起始
        container.innerHTML = '';
        for (let i = 0; i < 7; i++) {
            const d = addDays(startOfWeek, i);
            const dateStr = fmtDate(d);
            const isActive = isSameDay(d, state.selectedDate);
            const isToday = isSameDay(d, new Date());
            const hasTasks = state.tasks.some(t => t.date === dateStr && t.status === 'pending');

            const el = document.createElement('div');
            el.className = `date-item ${isActive ? 'active' : ''} ${isToday ? 'today' : ''}`;
            el.innerHTML = `
                <span class="day-name">周${weekdayNames[d.getDay()]}</span>
                <span class="day-num">${fmtDateShort(d)}</span>
                ${hasTasks ? '<span class="day-dot"></span>' : ''}
            `;
            el.addEventListener('click', () => {
                state.selectedDate = d;
                renderDateBar();
                renderTodayPage();
            });
            container.appendChild(el);
        }
    }

    $('#datePrevWeek').addEventListener('click', () => {
        state.selectedDate = addDays(state.selectedDate, -7);
        renderDateBar();
        renderTodayPage();
    });
    $('#dateNextWeek').addEventListener('click', () => {
        state.selectedDate = addDays(state.selectedDate, 7);
        renderDateBar();
        renderTodayPage();
    });

    // ===== TaskCard 渲染 =====
    function createTaskCard(task, options = {}) {
        const archive = state.archives.find(a => a.taskId === task.id);
        const isArchived = task.status === 'archived';
        const isOverdue = !isArchived && new Date(task.date) < new Date(fmtDate(new Date())) && task.date !== fmtDate(new Date());
        const showActions = options.showActions !== false;

        const card = document.createElement('div');
        card.className = `task-card ${isOverdue ? 'overdue' : ''} ${isArchived ? 'archived' : ''}`;

        let checkboxHtml = '';
        if (isArchived) {
            checkboxHtml = `<div class="task-checkbox archived-check"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></div>`;
        } else {
            checkboxHtml = `<div class="task-checkbox ${isArchived ? 'checked' : ''}" data-task-id="${task.id}"></div>`;
        }

        card.innerHTML = `
            ${checkboxHtml}
            <div class="task-content">
                <div class="task-title">${escapeHtml(task.name)}</div>
                ${task.standard ? `
                    <div class="task-standard">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/></svg>
                        ${escapeHtml(truncate(task.standard, 40))}
                    </div>
                ` : ''}
                <div class="task-meta">
                    ${task.relatedTaskIds?.length ? `<span class="task-meta-tag">周目标</span>` : ''}
                    <span class="task-meta-date">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                        ${isOverdue ? '逾期' : fmtDateCN(new Date(task.date))}
                    </span>
                    ${archive ? `
                        <span class="task-meta-score">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="#FBBF24" stroke="#FBBF24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                            ${archive.score} · ${archive.duration}min
                        </span>
                    ` : ''}
                    ${task.delayCount > 0 ? `<span class="badge badge-warning">已延期 ${task.delayCount} 次</span>` : ''}
                </div>
            </div>
            ${showActions && !isArchived ? `
                <div class="task-actions">
                    <button class="task-action-btn" data-action="edit" data-task-id="${task.id}" title="编辑">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button class="task-action-btn" data-action="delete" data-task-id="${task.id}" title="删除">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                </div>
            ` : ''}
        `;

        // Checkbox 点击归档
        const checkbox = card.querySelector('.task-checkbox:not(.archived-check)');
        if (checkbox && !isArchived) {
            checkbox.addEventListener('click', (e) => {
                e.stopPropagation();
                openArchiveDialog(task);
            });
        }

        // 操作按钮
        card.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const id = btn.dataset.taskId;
                if (action === 'edit') openTodoDialog(state.tasks.find(t => t.id === id));
                else if (action === 'delete') deleteTask(id);
            });
        });

        return card;
    }

    // ===== 今日首页 =====
    function renderTodayPage() {
        const dateStr = fmtDate(state.selectedDate);
        const todayTasks = state.tasks.filter(t => t.date === dateStr && t.kind === 'todo');
        const pendingCount = todayTasks.filter(t => t.status === 'pending').length;
        const archivedCount = todayTasks.filter(t => t.status === 'archived').length;
        const total = todayTasks.length;
        const progress = total > 0 ? (archivedCount / total * 100) : 0;

        // 更新表情
        const mood = moodEmojis.slice().reverse().find(m => progress >= m.threshold * 100) || moodEmojis[0];
        $('#todayMood').textContent = mood.emoji;
        $('#todayMoodText').textContent = mood.text;

        // 概览卡片
        $('#todayTodoCount').textContent = pendingCount;
        $('#todayProgressBar').style.width = `${progress}%`;
        $('#todayListCount').textContent = todayTasks.length;

        // 日记状态
        const diary = state.diaries.find(d => d.date === dateStr);
        const diaryBody = $('#diaryStatusBody');
        if (diary) {
            diaryBody.innerHTML = `
                <span class="stats-card-number" style="font-size: 18px; font-weight: 500; color: var(--success);">已记录 ✓</span>
                <span class="stats-card-unit">回顾今日</span>
            `;
            $('#btnGoDiary').textContent = '回顾今日';
        } else {
            diaryBody.innerHTML = `
                <span class="stats-card-number" style="font-size: 18px; font-weight: 500;">未记录</span>
                <span class="stats-card-unit">点击记录今日复盘</span>
            `;
            $('#btnGoDiary').textContent = '去写日记';
        }

        // 代办列表
        const list = $('#todayTaskList');
        list.innerHTML = '';
        if (todayTasks.length === 0) {
            list.innerHTML = `
                <div class="empty-state" style="padding: 32px;">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/></svg>
                    <p class="empty-title" style="font-size: 16px;">今天还没有代办</p>
                    <p class="empty-desc" style="font-size: 13px;">添加一个代办，开始高效的一天</p>
                </div>
            `;
        } else {
            todayTasks.forEach(task => list.appendChild(createTaskCard(task)));
        }
    }

    // ===== 代办列表页 =====
    function renderTodoPage() {
        const filter = state.todoFilter;
        let filtered = state.tasks.filter(t => t.kind === 'todo');

        if (filter === 'today') {
            filtered = filtered.filter(t => t.date === fmtDate(new Date()));
        } else if (filter === 'pending') {
            filtered = filtered.filter(t => t.status === 'pending');
        } else if (filter === 'overdue') {
            filtered = filtered.filter(t => t.status === 'pending' && new Date(t.date) < new Date(fmtDate(new Date())));
        } else if (filter === 'archived') {
            filtered = filtered.filter(t => t.status === 'archived');
        }

        const list = $('#todoTaskList');
        const empty = $('#todoEmptyState');
        list.innerHTML = '';

        if (filtered.length === 0) {
            list.style.display = 'none';
            empty.style.display = 'flex';
        } else {
            list.style.display = 'flex';
            empty.style.display = 'none';
            filtered.forEach(task => list.appendChild(createTaskCard(task, { showActions: filter !== 'archived' })));
        }
    }

    $$('.filter-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            $$('.filter-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            state.todoFilter = tab.dataset.filter;
            renderTodoPage();
        });
    });

    // ===== 弹窗控制 =====
    function openModal(id) {
        $('#modalOverlay').classList.add('show');
        $(id).classList.add('show');
        document.body.style.overflow = 'hidden';
    }
    function closeModal(id) {
        $('#modalOverlay').classList.remove('show');
        $(id).classList.remove('show');
        document.body.style.overflow = '';
    }
    function closeAllModals() {
        closeModal('#todoDialog');
        closeModal('#archiveDialog');
        closeModal('#goalDetailDialog');
        closeModal('#habitDetailDialog');
    }

    $('#modalOverlay').addEventListener('click', closeAllModals);
    $('#todoDialogClose').addEventListener('click', () => closeModal('#todoDialog'));
    $('#todoDialogCancel').addEventListener('click', () => closeModal('#todoDialog'));
    $('#archiveDialogClose').addEventListener('click', () => closeModal('#archiveDialog'));
    $('#archiveDialogCancel').addEventListener('click', () => closeModal('#archiveDialog'));
    $('#goalDetailClose').addEventListener('click', () => closeModal('#goalDetailDialog'));
    $('#goalDetailCancel').addEventListener('click', () => closeModal('#goalDetailDialog'));
    $('#habitDetailClose').addEventListener('click', () => closeModal('#habitDetailDialog'));
    $('#habitDetailCancel').addEventListener('click', () => closeModal('#habitDetailDialog'));

    // ===== 创建/编辑代办弹窗 =====
    function openTodoDialog(task = null) {
        state.editingTask = task;
        state.selectedRelatedGoals = task ? [...(task.relatedTaskIds || [])] : [];
        $('#todoDialogTitle').textContent = task ? '编辑代办' : '新建代办';
        $('#todoDialogConfirm').textContent = task ? '保存修改' : '创建代办';

        if (task) {
            $('#todoName').value = task.name;
            $('#todoRepeat').value = task.repeat;
            $('#todoDate').value = task.date;
            $('#todoDesc').value = task.description || '';
            $('#todoStandard').value = task.standard || '';
            $$(`input[name="delayPolicy"][value="${task.delayPolicy}"]`).forEach(el => el.checked = true);
        } else {
            $('#todoForm').reset();
            $('#todoDate').value = fmtDate(state.selectedDate);
            $$(`input[name="delayPolicy"][value="default"]`).forEach(el => el.checked = true);
        }

        // 渲染关联目标选择器（代办可关联周/月/年目标）
        renderRelatedGoalSelector('todo');
        // 重复联动
        onRepeatChange();
        openModal('#todoDialog');
    }

    function renderRelatedGoalSelector(kind, currentPeriod) {
        const dropdown = $('#relatedGoalDropdown');
        const list = $('#relatedGoalList');
        const trigger = $('#relatedGoalTrigger');
        const tags = $('#relatedGoalTags');

        // 按文档2.1规则过滤可关联目标
        let availableGoals = [];
        if (kind === 'todo') {
            // 代办可关联周/月/年目标
            availableGoals = state.goals.filter(g => g.kind === 'goal' && g.status === 'pending');
        } else if (kind === 'goal') {
            // 周→月/年，月→年
            if (currentPeriod === 'week') {
                availableGoals = state.goals.filter(g => g.kind === 'goal' && (g.period === 'month' || g.period === 'year') && g.status === 'pending');
            } else if (currentPeriod === 'month') {
                availableGoals = state.goals.filter(g => g.kind === 'goal' && g.period === 'year' && g.status === 'pending');
            } else {
                availableGoals = []; // 年目标不能再关联更高层
            }
        }

        // 排除自己
        if (state.editingTask) {
            availableGoals = availableGoals.filter(g => g.id !== state.editingTask.id);
        }

        // 渲染下拉列表
        if (availableGoals.length === 0) {
            list.innerHTML = '<div class="related-goal-empty">暂无可关联的目标</div>';
        } else {
            list.innerHTML = availableGoals.map(g => `
                <label class="related-goal-item">
                    <input type="checkbox" value="${g.id}" ${state.selectedRelatedGoals.includes(g.id) ? 'checked' : ''}>
                    <span class="goal-period-tag">${g.period === 'week' ? '周' : g.period === 'month' ? '月' : '年'}</span>
                    <span class="goal-name">${escapeHtml(g.name)}</span>
                </label>
            `).join('');
        }

        // 绑定选择事件
        list.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', () => {
                const gid = cb.value;
                if (cb.checked) {
                    if (!state.selectedRelatedGoals.includes(gid)) state.selectedRelatedGoals.push(gid);
                } else {
                    state.selectedRelatedGoals = state.selectedRelatedGoals.filter(id => id !== gid);
                }
                renderRelatedGoalTags();
            });
        });

        // 触发器点击展开/收起
        trigger.onclick = (e) => {
            e.stopPropagation();
            const isVisible = dropdown.style.display !== 'none';
            dropdown.style.display = isVisible ? 'none' : 'block';
        };

        // 点击外部收起
        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target) && e.target !== trigger) {
                dropdown.style.display = 'none';
            }
        });

        renderRelatedGoalTags();
    }

    function renderRelatedGoalTags() {
        const tags = $('#relatedGoalTags');
        if (state.selectedRelatedGoals.length === 0) {
            tags.innerHTML = '';
            $('#relatedGoalTriggerText').textContent = '选择要关联的目标…';
            return;
        }
        $('#relatedGoalTriggerText').textContent = `已选择 ${state.selectedRelatedGoals.length} 个目标`;
        tags.innerHTML = state.selectedRelatedGoals.map(gid => {
            const g = state.goals.find(x => x.id === gid);
            return g ? `
                <span class="related-goal-tag">
                    ${escapeHtml(g.name)}
                    <span class="remove-tag" data-gid="${g.id}">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </span>
                </span>
            ` : '';
        }).join('');

        tags.querySelectorAll('.remove-tag').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const gid = btn.dataset.gid;
                state.selectedRelatedGoals = state.selectedRelatedGoals.filter(id => id !== gid);
                // 同步更新下拉列表中的勾选状态
                const cb = $(`#relatedGoalList input[value="${gid}"]`);
                if (cb) cb.checked = false;
                renderRelatedGoalTags();
            });
        });
    }

    function onRepeatChange() {
        const val = $('#todoRepeat').value;
        $('#weeklyOptions').style.display = val === 'weekly' ? 'block' : 'none';
        $('#todoDateLabel').textContent = val === 'daily' ? '开始日期' : '计划日期';
    }
    $('#todoRepeat').addEventListener('change', onRepeatChange);

    $('#todoDialogConfirm').addEventListener('click', () => {
        const name = $('#todoName').value.trim();
        const standard = $('#todoStandard').value.trim();
        if (!name || !standard) {
            showInfoBar('请填写必填项', 'error');
            return;
        }

        const taskData = {
            name,
            repeat: $('#todoRepeat').value,
            date: $('#todoDate').value,
            delayPolicy: $('input[name="delayPolicy"]:checked').value,
            description: $('#todoDesc').value.trim(),
            standard,
            relatedTaskIds: [...state.selectedRelatedGoals]
        };

        const isGoal = state.editingTask && state.editingTask.kind === 'goal';
        const isNewGoal = !state.editingTask && $('#todoDialogTitle').textContent.includes('目标');

        if (state.editingTask) {
            Object.assign(state.editingTask, taskData, { updatedAt: new Date().toISOString() });
            showInfoBar(isGoal ? '目标已更新' : '代办已更新');
        } else {
            const newItem = {
                id: (isNewGoal ? 'g' : 't') + Date.now(),
                kind: isNewGoal ? 'goal' : 'todo',
                period: isNewGoal ? state.goalPeriod : 'day',
                ...taskData,
                status: 'pending',
                delayCount: 0,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            };
            if (isNewGoal) {
                state.goals.unshift(newItem);
                showInfoBar('目标已创建');
            } else {
                state.tasks.unshift(newItem);
                showInfoBar('代办已创建');
            }
        }

        closeModal('#todoDialog');
        renderTodayPage();
        renderTodoPage();
        renderGoalPage();
        renderDateBar();
    });

    // 新建代办按钮们
    $('#btnNewTodoToday').addEventListener('click', () => openTodoDialog());
    $('#btnNewTodo').addEventListener('click', () => openTodoDialog());
    $('#btnEmptyNewTodo').addEventListener('click', () => openTodoDialog());
    $('#btnAddTaskToday').addEventListener('click', () => openTodoDialog());

    // ===== 归档弹窗 =====
    function openArchiveDialog(task) {
        state.archivingTask = task;
        state.ratingValue = 0;

        $('#archiveTaskName').textContent = task.name;
        $('#archiveTaskDesc').textContent = task.description || '无描述';
        $('#archiveTaskStandard').textContent = task.standard || '无完成标准';
        $('#archiveDuration').value = '';
        $('#archiveSummary').value = '';
        $('#charCount').textContent = '已输入 0/500 字';
        updateRatingDisplay(0);

        // 快速标签
        $$('#quickDurationTags button').forEach(btn => btn.classList.remove('active'));

        openModal('#archiveDialog');
    }

    // 评分星星
    const ratingBtns = $$('#ratingWidget button');
    function updateRatingDisplay(value) {
        state.ratingValue = value;
        ratingBtns.forEach((btn, idx) => {
            btn.classList.toggle('filled', idx < value);
            btn.classList.remove('hovered');
        });
        const labels = ['', '⭐ 还需努力', '⭐ 勉强完成', '⭐ 基本达标', '⭐ 完成不错', '⭐ 完美达成'];
        const colors = ['', '#EF4444', '#F59E0B', '#009FAA', '#10B981', '#10B981'];
        const labelEl = $('#ratingLabel');
        labelEl.textContent = value > 0 ? labels[value] : '请点击星星评分';
        labelEl.style.color = value > 0 ? colors[value] : 'var(--text-tertiary)';
    }

    ratingBtns.forEach((btn, idx) => {
        btn.addEventListener('mouseenter', () => {
            ratingBtns.forEach((b, i) => {
                b.classList.toggle('hovered', i <= idx);
                b.classList.toggle('filled', i < state.ratingValue);
            });
        });
        btn.addEventListener('mouseleave', () => {
            ratingBtns.forEach((b, i) => {
                b.classList.remove('hovered');
                b.classList.toggle('filled', i < state.ratingValue);
            });
        });
        btn.addEventListener('click', () => updateRatingDisplay(idx + 1));
    });

    // 快速用时标签
    $$('#quickDurationTags button').forEach(btn => {
        btn.addEventListener('click', () => {
            $$('#quickDurationTags button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            $('#archiveDuration').value = btn.dataset.val;
        });
    });

    // 字数统计
    $('#archiveSummary').addEventListener('input', (e) => {
        const len = e.target.value.length;
        const el = $('#charCount');
        el.textContent = `已输入 ${len}/500 字`;
        el.classList.toggle('warning', len > 450);
    });

    $('#archiveDialogConfirm').addEventListener('click', () => {
        const duration = parseInt($('#archiveDuration').value, 10);
        if (!duration || duration <= 0) {
            showInfoBar('请填写代办用时', 'error');
            return;
        }
        if (state.ratingValue === 0) {
            showInfoBar('请评分', 'error');
            return;
        }

        // 归档
        state.archivingTask.status = 'archived';
        state.archivingTask.updatedAt = new Date().toISOString();
        state.archives.push({
            id: 'a' + Date.now(),
            taskId: state.archivingTask.id,
            duration,
            score: state.ratingValue,
            summary: $('#archiveSummary').value.trim(),
            archivedAt: new Date().toISOString()
        });

        showInfoBar('代办已归档，继续保持！');
        closeModal('#archiveDialog');
        renderTodayPage();
        renderTodoPage();
        renderDateBar();
        renderStatsPage();
    });

    // 删除任务
    function deleteTask(id) {
        if (!confirm('确定删除这条代办吗？')) return;
        state.tasks = state.tasks.filter(t => t.id !== id);
        showInfoBar('代办已删除');
        renderTodayPage();
        renderTodoPage();
    }

    // ===== 目标计划页 =====
    function renderGoalPage() {
        const period = state.goalPeriod;
        const filtered = state.goals.filter(g => g.period === period && g.kind === 'goal');
        const grid = $('#goalGrid');
        const empty = $('#goalEmptyState');
        grid.innerHTML = '';

        if (filtered.length === 0) {
            grid.style.display = 'none';
            empty.style.display = 'flex';
        } else {
            grid.style.display = 'grid';
            empty.style.display = 'none';
            filtered.forEach(goal => grid.appendChild(createGoalCard(goal)));
        }
    }

    function createGoalCard(goal) {
        const relatedTasks = state.tasks.filter(t => goal.relatedTaskIds.includes(t.id) && t.kind === 'todo');
        const completedTasks = relatedTasks.filter(t => t.status === 'archived');
        const progress = relatedTasks.length > 0 ? Math.round(completedTasks.length / relatedTasks.length * 100) : 0;
        const isArchived = goal.status === 'archived';

        const card = document.createElement('div');
        card.className = `goal-card ${isArchived ? 'archived' : ''}`;

        // 环形进度条 SVG
        const radius = 52;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (progress / 100) * circumference;

        card.innerHTML = `
            <div class="goal-card-header">
                <div class="goal-card-info">
                    <div class="goal-card-title">${escapeHtml(goal.name)}</div>
                    <div class="goal-card-desc">${escapeHtml(goal.description || '暂无描述')}</div>
                </div>
                <div class="goal-card-progress-ring">
                    <svg viewBox="0 0 120 120">
                        <circle class="progress-ring-bg" cx="60" cy="60" r="52"/>
                        <circle class="progress-ring-fill" cx="60" cy="60" r="52"
                            stroke-dasharray="${circumference}"
                            stroke-dashoffset="${offset}"/>
                    </svg>
                    <div class="goal-card-progress-text">${progress}%</div>
                </div>
            </div>
            <div class="goal-card-footer">
                <div class="goal-card-meta">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                    ${completedTasks.length}/${relatedTasks.length} 已完成
                    ${isArchived ? '<span class="badge badge-success" style="margin-left:8px">已归档</span>' : ''}
                </div>
                <div class="goal-card-actions">
                    <button class="goal-card-action-btn" data-action="view" data-goal-id="${goal.id}" title="查看详情">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                    <button class="goal-card-action-btn" data-action="edit" data-goal-id="${goal.id}" title="编辑">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button class="goal-card-action-btn" data-action="delete" data-goal-id="${goal.id}" title="删除">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                </div>
            </div>
        `;

        card.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const id = btn.dataset.goalId;
                if (action === 'view') openGoalDetailDialog(state.goals.find(g => g.id === id));
                else if (action === 'edit') openGoalDialog(state.goals.find(g => g.id === id));
                else if (action === 'delete') deleteGoal(id);
            });
        });

        card.addEventListener('click', () => openGoalDetailDialog(goal));
        return card;
    }

    // 目标 Tab 切换
    $$('.goal-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            $$('.goal-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            state.goalPeriod = tab.dataset.period;
            renderGoalPage();
        });
    });

    // 新建目标
    $('#btnNewGoal').addEventListener('click', () => openGoalDialog());
    $('#btnEmptyNewGoal').addEventListener('click', () => openGoalDialog());

    function openGoalDialog(goal = null) {
        state.editingTask = goal;
        state.selectedRelatedGoals = goal ? [...(goal.relatedTaskIds || [])] : [];
        $('#todoDialogTitle').textContent = goal ? '编辑目标' : '新建目标';
        $('#todoDialogConfirm').textContent = goal ? '保存修改' : '创建目标';

        if (goal) {
            $('#todoName').value = goal.name;
            $('#todoRepeat').value = goal.repeat || 'none';
            $('#todoDate').value = goal.date;
            $('#todoDesc').value = goal.description || '';
            $('#todoStandard').value = goal.standard || '';
            $$(`input[name="delayPolicy"][value="${goal.delayPolicy}"]`).forEach(el => el.checked = true);
        } else {
            $('#todoForm').reset();
            $('#todoDate').value = fmtDate(new Date());
            $$(`input[name="delayPolicy"][value="default"]`).forEach(el => el.checked = true);
        }

        // 渲染关联目标选择器（目标按周期层级关联：周→月/年，月→年）
        const currentPeriod = goal ? goal.period : state.goalPeriod;
        renderRelatedGoalSelector('goal', currentPeriod);
        onRepeatChange();
        openModal('#todoDialog');
    }

    // 目标详情弹窗
    function openGoalDetailDialog(goal) {
        $('#goalDetailTitle').textContent = goal.period === 'week' ? '周目标详情' : goal.period === 'month' ? '月目标详情' : '年目标详情';
        $('#goalDetailName').textContent = goal.name;
        $('#goalDetailDesc').textContent = goal.description || '暂无描述';

        // 计算进度
        const relatedTasks = state.tasks.filter(t => goal.relatedTaskIds.includes(t.id) && t.kind === 'todo');
        const completedTasks = relatedTasks.filter(t => t.status === 'archived');
        const progress = relatedTasks.length > 0 ? Math.round(completedTasks.length / relatedTasks.length * 100) : 0;

        // 环形进度条
        const radius = 52;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (progress / 100) * circumference;
        $('#goalDetailProgressCircle').setAttribute('stroke-dasharray', circumference);
        $('#goalDetailProgressCircle').setAttribute('stroke-dashoffset', offset);
        $('#goalDetailProgressText').textContent = progress + '%';

        // 标签
        const tagsEl = $('#goalDetailTags');
        tagsEl.innerHTML = `
            <span class="task-meta-tag">${goal.period === 'week' ? '周目标' : goal.period === 'month' ? '月目标' : '年目标'}</span>
            ${goal.status === 'archived' ? '<span class="badge badge-success">已归档</span>' : ''}
        `;

        // 关联代办列表
        const taskListEl = $('#goalDetailTaskList');
        $('#goalDetailTaskCount').textContent = relatedTasks.length;
        if (relatedTasks.length === 0) {
            taskListEl.innerHTML = '<div style="color: var(--text-tertiary); font-size: 13px; padding: 8px 0;">暂无关联代办</div>';
        } else {
            taskListEl.innerHTML = relatedTasks.map(t => `
                <div class="goal-detail-task-item">
                    <div class="task-check ${t.status === 'archived' ? 'checked' : ''}">
                        ${t.status === 'archived' ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>' : ''}
                    </div>
                    <span class="task-name ${t.status === 'archived' ? 'done' : ''}">${escapeHtml(t.name)}</span>
                    <span class="task-date">${fmtDateCN(new Date(t.date))}</span>
                </div>
            `).join('');
        }

        // 子目标列表（低周期目标关联到高周期目标）
        const subGoals = state.goals.filter(g => goal.relatedTaskIds.includes(g.id) && g.kind === 'goal');
        const subListEl = $('#goalDetailSubList');
        $('#goalDetailSubCount').textContent = subGoals.length;
        if (subGoals.length === 0) {
            subListEl.innerHTML = '<div style="color: var(--text-tertiary); font-size: 13px; padding: 8px 0;">暂无子目标</div>';
        } else {
            subListEl.innerHTML = subGoals.map(g => {
                const gTasks = state.tasks.filter(t => g.relatedTaskIds.includes(t.id) && t.kind === 'todo');
                const gCompleted = gTasks.filter(t => t.status === 'archived');
                const gProgress = gTasks.length > 0 ? Math.round(gCompleted.length / gTasks.length * 100) : 0;
                return `
                    <div class="goal-detail-sub-item">
                        <span class="sub-name">${escapeHtml(g.name)}</span>
                        <div class="sub-progress-bar"><div class="fill" style="width: ${gProgress}%"></div></div>
                        <span class="sub-percent">${gProgress}%</span>
                    </div>
                `;
            }).join('');
        }

        // 编辑按钮
        $('#goalDetailEdit').onclick = () => {
            closeModal('#goalDetailDialog');
            openGoalDialog(goal);
        };

        openModal('#goalDetailDialog');
    }

    function deleteGoal(id) {
        if (!confirm('确定删除这个目标吗？关联关系将一并移除。')) return;
        state.goals = state.goals.filter(g => g.id !== id);
        // 清理其他目标中的关联
        state.goals.forEach(g => {
            g.relatedTaskIds = g.relatedTaskIds.filter(rid => rid !== id);
        });
        showInfoBar('目标已删除');
        renderGoalPage();
    }

    // ===== 习惯养成页 =====
    function renderHabitPage() {
        const grid = $('#habitGrid');
        const empty = $('#habitEmptyState');
        grid.innerHTML = '';

        const activeHabits = state.habits.filter(h => h.status === 'active');
        if (activeHabits.length === 0) {
            grid.style.display = 'none';
            empty.style.display = 'flex';
        } else {
            grid.style.display = 'grid';
            empty.style.display = 'none';
            activeHabits.forEach(habit => grid.appendChild(createHabitCard(habit)));
        }
    }

    function getStreak(records) {
        const dates = Object.keys(records).sort().reverse();
        let streak = 0;
        const today = fmtDate(new Date());
        const yesterday = fmtDate(addDays(new Date(), -1));
        let expectDate = today;
        for (const d of dates) {
            if (d > today) continue;
            if (d === expectDate && records[d]) {
                streak++;
                expectDate = fmtDate(addDays(new Date(expectDate), -1));
            } else if (d === expectDate && !records[d]) {
                if (expectDate === today) {
                    expectDate = yesterday;
                    continue;
                }
                break;
            } else if (d < expectDate) {
                break;
            }
        }
        return streak;
    }

    function getMonthCount(records) {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth();
        return Object.entries(records).filter(([date, checked]) => {
            const d = new Date(date);
            return checked && d.getFullYear() === year && d.getMonth() === month;
        }).length;
    }

    function getMaxStreak(records) {
        const sortedDates = Object.keys(records).sort();
        let maxStreak = 0;
        let current = 0;
        let prev = null;
        for (const d of sortedDates) {
            if (!records[d]) {
                maxStreak = Math.max(maxStreak, current);
                current = 0;
                prev = null;
                continue;
            }
            if (prev === null) {
                current = 1;
            } else {
                const diff = (new Date(d) - new Date(prev)) / (1000 * 60 * 60 * 24);
                if (diff === 1) current++;
                else current = 1;
            }
            prev = d;
        }
        return Math.max(maxStreak, current);
    }

    function createHabitCard(habit) {
        const todayStr = fmtDate(new Date());
        const isChecked = !!habit.records[todayStr];
        const streak = getStreak(habit.records);
        const card = document.createElement('div');
        card.className = 'habit-card';

        card.innerHTML = `
            <div class="habit-card-header">
                <div class="habit-card-name">${escapeHtml(habit.name)}</div>
                <div class="habit-card-actions">
                    <button class="habit-card-action-btn" data-action="view" data-habit-id="${habit.id}" title="详情">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                    <button class="habit-card-action-btn" data-action="delete" data-habit-id="${habit.id}" title="删除">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                </div>
            </div>
            <div class="habit-card-streak">
                <div class="habit-streak-number">${streak}</div>
                <div class="habit-streak-label">连续打卡天数</div>
            </div>
            <button class="habit-check-btn ${isChecked ? 'checked' : ''}" data-habit-id="${habit.id}">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </button>
            <div class="habit-card-meta">今天 ${isChecked ? '已打卡 ✓' : '未打卡'}</div>
        `;

        // 打卡按钮
        const checkBtn = card.querySelector('.habit-check-btn');
        checkBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            habit.records[todayStr] = !isChecked;
            renderHabitPage();
            showInfoBar(isChecked ? '已取消打卡' : '打卡成功！继续保持');
        });

        // 操作按钮
        card.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const id = btn.dataset.habitId;
                if (action === 'view') openHabitDetailDialog(state.habits.find(h => h.id === id));
                else if (action === 'delete') deleteHabit(id);
            });
        });

        card.addEventListener('click', () => openHabitDetailDialog(habit));
        return card;
    }

    function openHabitDetailDialog(habit) {
        const streak = getStreak(habit.records);
        const monthCount = getMonthCount(habit.records);
        const maxStreak = getMaxStreak(habit.records);

        $('#habitDetailTitle').textContent = habit.status === 'ended' ? '已结束的习惯' : '习惯详情';
        $('#habitStreakNumber').textContent = streak;
        $('#habitDetailName').textContent = habit.name;
        $('#habitDetailDesc').textContent = habit.description || '暂无描述';
        $('#habitMonthCount').textContent = monthCount;
        $('#habitMaxStreak').textContent = maxStreak;

        // 月度日历
        const cal = $('#habitDetailCalendar');
        cal.innerHTML = '';
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startOffset = firstDay.getDay();

        // 星期标题
        weekdayNames.forEach(name => {
            const el = document.createElement('div');
            el.className = 'habit-cal-weekday';
            el.textContent = name;
            cal.appendChild(el);
        });

        // 填充
        for (let i = 0; i < startOffset; i++) {
            const el = document.createElement('div');
            el.className = 'habit-cal-day';
            el.style.visibility = 'hidden';
            cal.appendChild(el);
        }
        for (let d = 1; d <= lastDay.getDate(); d++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            const isChecked = !!habit.records[dateStr];
            const isToday = dateStr === fmtDate(new Date());
            const el = document.createElement('div');
            el.className = `habit-cal-day ${isChecked ? 'checked' : ''} ${isToday ? 'today' : ''}`;
            el.textContent = d;
            cal.appendChild(el);
        }

        // 结束习惯按钮
        const endBtn = $('#habitDetailEnd');
        endBtn.textContent = habit.status === 'ended' ? '恢复习惯' : '结束习惯';
        endBtn.style.background = habit.status === 'ended' ? 'var(--primary)' : 'var(--danger)';
        endBtn.onclick = () => {
            habit.status = habit.status === 'ended' ? 'active' : 'ended';
            closeModal('#habitDetailDialog');
            renderHabitPage();
            showInfoBar(habit.status === 'ended' ? '习惯已结束' : '习惯已恢复');
        };

        $('#habitDetailCancel').onclick = () => closeModal('#habitDetailDialog');
        $('#habitDetailClose').onclick = () => closeModal('#habitDetailDialog');

        openModal('#habitDetailDialog');
    }

    function deleteHabit(id) {
        if (!confirm('确定删除这个习惯吗？打卡记录将一并删除。')) return;
        state.habits = state.habits.filter(h => h.id !== id);
        showInfoBar('习惯已删除');
        renderHabitPage();
    }

    $('#btnNewHabit').addEventListener('click', () => {
        showInfoBar('新建习惯功能暂未实现，敬请期待');
    });
    $('#btnEmptyNewHabit').addEventListener('click', () => {
        showInfoBar('新建习惯功能暂未实现，敬请期待');
    });

    // ===== 日记页 =====
    let diaryCalendarDate = new Date();

    function renderDiaryPage() {
        renderDiaryCalendar();
        renderDiaryRecentList();
        renderDiaryEditor();
    }

    function renderDiaryCalendar() {
        const container = $('#diaryCalendar');
        const year = diaryCalendarDate.getFullYear();
        const month = diaryCalendarDate.getMonth();
        $('#calMonthYear').textContent = `${year}年${month + 1}月`;

        container.innerHTML = '';

        // 星期标题
        weekdayNames.forEach((name, i) => {
            const el = document.createElement('div');
            el.className = 'cal-weekday';
            el.textContent = name;
            container.appendChild(el);
        });

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startOffset = firstDay.getDay(); // 0=周日

        // 上月填充
        for (let i = 0; i < startOffset; i++) {
            const d = new Date(year, month, -startOffset + i + 1);
            const el = document.createElement('div');
            el.className = 'cal-day other-month';
            el.textContent = d.getDate();
            container.appendChild(el);
        }

        // 当月
        for (let d = 1; d <= lastDay.getDate(); d++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            const dateObj = new Date(year, month, d);
            const isSelected = fmtDate(state.diarySelectedDate) === dateStr;
            const isToday = isSameDay(dateObj, new Date());
            const hasDiary = state.diaries.some(diary => diary.date === dateStr);

            const el = document.createElement('div');
            el.className = `cal-day ${isSelected ? 'selected' : ''} ${isToday ? 'today' : ''} ${hasDiary ? 'has-diary' : ''}`;
            el.textContent = d;
            el.addEventListener('click', () => {
                state.diarySelectedDate = dateObj;
                renderDiaryCalendar();
                renderDiaryEditor();
            });
            container.appendChild(el);
        }
    }

    $('#calPrevMonth').addEventListener('click', () => {
        diaryCalendarDate.setMonth(diaryCalendarDate.getMonth() - 1);
        renderDiaryCalendar();
    });
    $('#calNextMonth').addEventListener('click', () => {
        diaryCalendarDate.setMonth(diaryCalendarDate.getMonth() + 1);
        renderDiaryCalendar();
    });

    function renderDiaryRecentList() {
        const list = $('#diaryRecentList');
        list.innerHTML = '';
        const sorted = [...state.diaries].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 10);
        sorted.forEach(diary => {
            const d = new Date(diary.date);
            const isSelected = fmtDate(state.diarySelectedDate) === diary.date;
            const item = document.createElement('div');
            item.className = `diary-recent-item ${isSelected ? 'active' : ''}`;
            item.innerHTML = `
                <span>
                    <span class="diary-recent-date">${fmtDateShort(d)}</span>
                    <span class="diary-recent-weekday">周${weekdayNames[d.getDay()]}</span>
                </span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/></svg>
            `;
            item.addEventListener('click', () => {
                state.diarySelectedDate = d;
                renderDiaryCalendar();
                renderDiaryEditor();
                renderDiaryRecentList();
            });
            list.appendChild(item);
        });
    }

    function renderDiaryEditor() {
        const container = $('#diaryMain');
        const dateStr = fmtDate(state.diarySelectedDate);
        const diary = state.diaries.find(d => d.date === dateStr);
        const dateTitle = `${state.diarySelectedDate.getFullYear()}年${state.diarySelectedDate.getMonth() + 1}月${state.diarySelectedDate.getDate()}日 周${weekdayNames[state.diarySelectedDate.getDay()]}`;

        if (!diary) {
            container.innerHTML = `
                <div class="diary-editor-header">
                    <div class="diary-editor-title">${dateTitle}</div>
                </div>
                <div class="diary-guide">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                    <h3>今天还没有写日记</h3>
                    <p>记录今日复盘，沉淀每一天的成长</p>
                    <button class="btn btn-primary" id="btnStartDiary">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                        开始记录今日复盘
                    </button>
                    <small>今日数据将在保存时自动汇总</small>
                </div>
            `;
            $('#btnStartDiary').addEventListener('click', () => createDiary(dateStr));
            return;
        }

        container.innerHTML = `
            <div class="diary-editor-header">
                <div class="diary-editor-title">${dateTitle}</div>
                <div class="diary-editor-actions">
                    <button class="btn btn-primary" id="btnSaveDiary">保存</button>
                    <button class="btn btn-ghost" style="color: var(--danger);" id="btnDeleteDiary">删除</button>
                </div>
            </div>
            <div class="diary-summary-card">
                <div class="diary-summary-title">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>
                    今日自动汇总（只读）
                </div>
                ${renderAutoSummary(diary.autoSummary)}
                <div class="diary-summary-hint">以上数据为创建日记时的快照，修改代办记录不会同步更新</div>
            </div>
            <div class="diary-editor-toolbar">
                <span class="diary-editor-label">自由书写区</span>
                <div class="diary-editor-modes">
                    <button class="diary-mode-btn ${state.diaryEditorMode === 'edit' ? 'active' : ''}" data-mode="edit" id="btnModeEdit">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                        编辑
                    </button>
                    <button class="diary-mode-btn ${state.diaryEditorMode === 'preview' ? 'active' : ''}" data-mode="preview" id="btnModePreview">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        预览
                    </button>
                </div>
            </div>
            <div class="diary-editor-area">
                <textarea class="diary-textarea" id="diaryContent" placeholder="# 今日复盘\n\n写下今天的收获、反思或明天的计划…" style="display: ${state.diaryEditorMode === 'edit' ? 'block' : 'none'};">${escapeHtml(diary.content)}</textarea>
                <div class="diary-preview" id="diaryPreview" style="display: ${state.diaryEditorMode === 'preview' ? 'block' : 'none'};">${renderMarkdown(diary.content)}</div>
            </div>
        `;

        // 编辑/预览切换
        $('#btnModeEdit').addEventListener('click', () => {
            state.diaryEditorMode = 'edit';
            renderDiaryEditor();
        });
        $('#btnModePreview').addEventListener('click', () => {
            state.diaryEditorMode = 'preview';
            renderDiaryEditor();
        });
        // 实时预览：编辑时同步更新预览内容
        const textarea = $('#diaryContent');
        if (textarea) {
            textarea.addEventListener('input', () => {
                const preview = $('#diaryPreview');
                if (preview) preview.innerHTML = renderMarkdown(textarea.value);
            });
        }

        $('#btnSaveDiary').addEventListener('click', () => {
            diary.content = $('#diaryContent').value;
            diary.updatedAt = new Date().toISOString();
            showInfoBar('日记已保存');
            renderDiaryRecentList();
        });
        $('#btnDeleteDiary').addEventListener('click', () => {
            if (!confirm('确定删除这篇日记吗？')) return;
            state.diaries = state.diaries.filter(d => d.id !== diary.id);
            showInfoBar('日记已删除');
            renderDiaryEditor();
            renderDiaryRecentList();
            renderDiaryCalendar();
        });
    }

    function renderAutoSummary(summary) {
        if (!summary) return '<div class="diary-summary-section">暂无数据</div>';
        let html = '';

        if (summary.tasks?.length) {
            html += `
                <div class="diary-summary-section">
                    <div class="diary-summary-section-title">今日完成代办（${summary.tasks.length}项）</div>
                    ${summary.tasks.map(t => `
                        <div class="diary-summary-item">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                            ${escapeHtml(t.name)} — ${'⭐'.repeat(t.score)} · ${t.duration}分钟
                        </div>
                    `).join('')}
                </div>
            `;
        }

        if (summary.habits?.length) {
            html += `
                <div class="diary-summary-section">
                    <div class="diary-summary-section-title">习惯打卡</div>
                    ${summary.habits.map(h => `
                        <div class="diary-summary-item">
                            ${h.checked
                                ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
                                : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
                            }
                            ${escapeHtml(h.name)}
                        </div>
                    `).join('')}
                </div>
            `;
        }

        if (summary.goals?.length) {
            html += `
                <div class="diary-summary-section">
                    <div class="diary-summary-section-title">关联目标进度变化</div>
                    ${summary.goals.map(g => `
                        <div class="diary-summary-item">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
                            ${escapeHtml(g.name)}：${g.oldProgress}% → ${g.newProgress}%
                        </div>
                    `).join('')}
                </div>
            `;
        }

        return html;
    }

    function createDiary(dateStr) {
        // 自动生成汇总
        const dayTasks = state.tasks.filter(t => t.date === dateStr && t.status === 'archived');
        const taskSummaries = dayTasks.map(t => {
            const arc = state.archives.find(a => a.taskId === t.id);
            return { name: t.name, score: arc?.score || 3, duration: arc?.duration || 30 };
        });

        const newDiary = {
            id: 'd' + Date.now(),
            date: dateStr,
            autoSummary: {
                tasks: taskSummaries,
                habits: [
                    { name: '早起', checked: Math.random() > 0.3 },
                    { name: '喝水', checked: Math.random() > 0.2 },
                    { name: '冥想', checked: Math.random() > 0.5 }
                ],
                goals: taskSummaries.length > 0 ? [{ name: '周目标·自我提升', oldProgress: 60, newProgress: Math.min(100, 60 + taskSummaries.length * 10) }] : []
            },
            content: '',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
        state.diaries.push(newDiary);
        state.diaries.sort((a, b) => b.date.localeCompare(a.date));
        renderDiaryEditor();
        renderDiaryRecentList();
        renderDiaryCalendar();
        showInfoBar('日记已创建，开始记录吧');
    }

    // 日记快捷入口
    $('#btnWriteDiaryToday').addEventListener('click', () => {
        switchPage('diary');
    });
    $('#btnGoDiary').addEventListener('click', () => {
        switchPage('diary');
    });

    // ===== 统计页 =====
    function renderStatsPage() {
        // 计算统计数据
        const allTasks = state.tasks.filter(t => t.kind === 'todo');
        const archived = allTasks.filter(t => t.status === 'archived');
        const rate = allTasks.length > 0 ? Math.round(archived.length / allTasks.length * 100) : 0;

        const avgScore = state.archives.length > 0
            ? (state.archives.reduce((s, a) => s + a.score, 0) / state.archives.length).toFixed(1)
            : '0.0';

        $('#statsRate').textContent = rate + '%';
        $('#statsScore').textContent = avgScore;

        renderHeatmap();
        renderBarChart();
    }

    function renderHeatmap() {
        const container = $('#heatmap');
        container.innerHTML = '';

        const today = new Date();
        const year = today.getFullYear();
        const months = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];

        // 生成最近 28 周的数据
        const weeks = [];
        for (let w = 0; w < 28; w++) {
            const weekDays = [];
            for (let d = 0; d < 7; d++) {
                const date = addDays(today, -(27 - w) * 7 - (6 - d));
                weekDays.push({
                    date,
                    dateStr: fmtDate(date),
                    count: state.heatmapData[fmtDate(date)] || 0
                });
            }
            weeks.push(weekDays);
        }

        // 月份标签
        const monthsRow = document.createElement('div');
        monthsRow.className = 'heatmap-months';
        // 简化：不精确对齐月份，只显示几个
        const seenMonths = new Set();
        weeks.forEach((week, wi) => {
            const midDay = week[3];
            const m = midDay.date.getMonth();
            if (!seenMonths.has(m) && wi % 4 === 0) {
                seenMonths.add(m);
                const label = document.createElement('div');
                label.className = 'heatmap-month-label';
                label.style.width = '60px';
                label.textContent = months[m];
                monthsRow.appendChild(label);
            }
        });
        container.appendChild(monthsRow);

        // 星期 + 格子
        const weekdayShort = ['日','一','二','三','四','五','六'];
        for (let d = 0; d < 7; d++) {
            const row = document.createElement('div');
            row.className = 'heatmap-row';

            const label = document.createElement('div');
            label.className = 'heatmap-weekday';
            label.textContent = weekdayShort[d];
            row.appendChild(label);

            const cells = document.createElement('div');
            cells.className = 'heatmap-cells';

            weeks.forEach(week => {
                const day = week[d];
                const cell = document.createElement('div');
                cell.className = 'heatmap-cell';
                cell.title = `${day.dateStr} · ${day.count} 项代办已归档`;

                const colors = ['var(--bg-secondary)', '#B3E5E9', '#66CDD6', '#009FAA', '#007A82'];
                const colorIdx = Math.min(day.count, colors.length - 1);
                cell.style.background = colors[colorIdx];

                cells.appendChild(cell);
            });

            row.appendChild(cells);
            container.appendChild(row);
        }
    }

    function renderBarChart() {
        const container = $('#barChart');
        container.innerHTML = '';

        // 最近 7 天的完成率
        const days = [];
        for (let i = 6; i >= 0; i--) {
            const d = addDays(new Date(), -i);
            const dateStr = fmtDate(d);
            const dayTasks = state.tasks.filter(t => t.date === dateStr && t.kind === 'todo');
            const archived = dayTasks.filter(t => t.status === 'archived');
            const rate = dayTasks.length > 0 ? Math.round(archived.length / dayTasks.length * 100) : 0;
            days.push({ label: fmtDateShort(d), rate });
        }

        const maxRate = Math.max(...days.map(d => d.rate), 100);

        days.forEach(day => {
            const item = document.createElement('div');
            item.className = 'bar-chart-item';
            item.innerHTML = `
                <div class="bar-chart-bar" style="height: ${(day.rate / maxRate * 100)}%;"></div>
                <div class="bar-chart-label">${day.label}</div>
            `;
            container.appendChild(item);
        });
    }

    $$('.pill-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            $$('.pill-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            // 实际应该根据 range 重新计算，这里简单刷新
            renderStatsPage();
        });
    });

    // ===== Markdown 实时渲染 =====
    function renderMarkdown(text) {
        if (!text) return '<p style="color: var(--text-tertiary); font-style: italic;">开始书写你的今日复盘…</p>';
        let html = escapeHtml(text);

        // 代码块
        html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        // 行内代码
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        // 标题
        html = html.replace(/^###### (.*$)/gim, '<h6>$1</h6>');
        html = html.replace(/^##### (.*$)/gim, '<h5>$1</h5>');
        html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
        // 粗体
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');
        // 斜体
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        html = html.replace(/_(.*?)_/g, '<em>$1</em>');
        // 删除线
        html = html.replace(/~~(.*?)~~/g, '<del>$1</del>');
        // 引用
        html = html.replace(/^&gt; (.*$)/gim, '<blockquote>$1</blockquote>');
        // 无序列表
        html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
        html = html.replace(/<\/ul>\s*<ul>/g, '');
        // 有序列表
        html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>');
        // 分割线
        html = html.replace(/^---+$/gim, '<hr>');
        html = html.replace(/^\*\*\*+$/gim, '<hr>');
        // 链接
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        // 段落
        html = html.replace(/\n\n/g, '</p><p>');
        html = '<p>' + html + '</p>';
        // 清理空段落
        html = html.replace(/<p><\/p>/g, '');
        html = html.replace(/<p>(<h[1-6]>.*<\/h[1-6]>)<\/p>/g, '$1');
        html = html.replace(/<p>(<blockquote>.*<\/blockquote>)<\/p>/g, '$1');
        html = html.replace(/<p>(<ul>.*<\/ul>)<\/p>/g, '$1');
        html = html.replace(/<p>(<pre>.*<\/pre>)<\/p>/g, '$1');
        html = html.replace(/<p>(<hr>)<\/p>/g, '$1');

        return html;
    }

    // ===== 辅助函数 =====
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    function truncate(text, len) {
        if (!text) return '';
        return text.length > len ? text.slice(0, len) + '…' : text;
    }

    // ===== 初始化 =====
    function init() {
        renderDateBar();
        renderTodayPage();
        renderTodoPage();
        renderGoalPage();
        renderHabitPage();
        renderDiaryPage();
        renderStatsPage();

        // 默认显示今日页
        switchPage('today');
    }

    init();
})();
