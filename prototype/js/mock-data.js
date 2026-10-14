/* ============================================
   拾光 · Mock 数据
   ============================================ */

const MOCK_DATA = {
    // 代办任务
    tasks: [
        {
            id: 't1',
            name: '阅读《设计心理学》chapter 3',
            kind: 'todo',
            period: 'day',
            repeat: 'none',
            date: new Date().toISOString().split('T')[0],
            delayPolicy: 'default',
            delayCount: 0,
            relatedTaskIds: [],
            description: '准备读书笔记，用于周末分享',
            standard: '写3条读书笔记，能复述核心观点',
            status: 'pending',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        },
        {
            id: 't2',
            name: '晨跑 5 公里',
            kind: 'todo',
            period: 'day',
            repeat: 'daily',
            date: new Date().toISOString().split('T')[0],
            delayPolicy: 'never',
            delayCount: 0,
            relatedTaskIds: [],
            description: '',
            standard: '配速低于 6:00，跑后拉伸',
            status: 'pending',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        },
        {
            id: 't3',
            name: '整理电脑桌面文件',
            kind: 'todo',
            period: 'day',
            repeat: 'none',
            date: new Date().toISOString().split('T')[0],
            delayPolicy: 'auto',
            delayCount: 0,
            relatedTaskIds: [],
            description: '',
            standard: '收件箱清空，桌面仅保留本周项目文件夹',
            status: 'pending',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        },
        {
            id: 't4',
            name: '完成周报撰写',
            kind: 'todo',
            period: 'day',
            repeat: 'weekly',
            date: '2026-01-14',
            delayPolicy: 'default',
            delayCount: 1,
            relatedTaskIds: [],
            description: '汇总本周工作进展与下周计划',
            standard: '覆盖所有项目，包含数据指标',
            status: 'archived',
            createdAt: '2026-01-13T10:00:00Z',
            updatedAt: '2026-01-15T16:00:00Z'
        },
        {
            id: 't5',
            name: '复习英语单词 50 个',
            kind: 'todo',
            period: 'day',
            repeat: 'daily',
            date: '2026-01-15',
            delayPolicy: 'default',
            delayCount: 0,
            relatedTaskIds: [],
            description: '',
            standard: '能正确拼写并说出中文意思',
            status: 'archived',
            createdAt: '2026-01-15T08:00:00Z',
            updatedAt: '2026-01-15T20:00:00Z'
        }
    ],

    // 归档记录
    archives: [
        {
            id: 'a1',
            taskId: 't4',
            duration: 45,
            score: 4,
            summary: '本周进展不错，但需要更多数据支撑',
            archivedAt: '2026-01-15T16:00:00Z'
        },
        {
            id: 'a2',
            taskId: 't5',
            duration: 30,
            score: 5,
            summary: '全部记住，效果不错',
            archivedAt: '2026-01-15T20:00:00Z'
        }
    ],

    // 日记
    diaries: [
        {
            id: 'd1',
            date: '2026-01-15',
            autoSummary: {
                tasks: [
                    { name: '完成周报撰写', score: 4, duration: 45 },
                    { name: '复习英语单词 50 个', score: 5, duration: 30 }
                ],
                habits: [
                    { name: '早起', checked: true },
                    { name: '喝水', checked: true },
                    { name: '冥想', checked: false }
                ],
                goals: [
                    { name: '周目标·自我提升', oldProgress: 60, newProgress: 80 }
                ]
            },
            content: '# 今日复盘\n\n今天读完第三章，关于心智模型的部分很有启发。\n\n> 用户的心理模型往往与设计师的模型不一致，好的设计应该弥合这一差距。\n\n明天需要把这部分内容整理成思维导图。',
            createdAt: '2026-01-15T22:00:00Z',
            updatedAt: '2026-01-15T22:30:00Z'
        },
        {
            id: 'd2',
            date: '2026-01-14',
            autoSummary: {
                tasks: [
                    { name: '代码审查', score: 4, duration: 60 }
                ],
                habits: [
                    { name: '早起', checked: true },
                    { name: '喝水', checked: false }
                ],
                goals: []
            },
            content: '今天主要在做代码审查，发现了几处潜在的内存泄漏问题。\n\n需要提醒团队在下次迭代中注意。',
            createdAt: '2026-01-14T21:00:00Z',
            updatedAt: '2026-01-14T21:00:00Z'
        },
        {
            id: 'd3',
            date: '2026-01-10',
            autoSummary: {
                tasks: [
                    { name: '项目规划会议', score: 5, duration: 90 }
                ],
                habits: [],
                goals: []
            },
            content: '项目规划会议很顺利，确定了 Q1 的里程碑。',
            createdAt: '2026-01-10T20:00:00Z',
            updatedAt: '2026-01-10T20:00:00Z'
        }
    ],

    // 热力图数据 (date -> count)
    heatmapData: (() => {
        const data = {};
        const today = new Date('2026-01-17');
        for (let i = 0; i < 365; i++) {
            const d = new Date(today);
            d.setDate(d.getDate() - i);
            const dateStr = d.toISOString().split('T')[0];
            // 随机生成 0-5 的数据，但让近期数据更丰富
            const rand = Math.random();
            let count = 0;
            if (rand > 0.4) count = 1;
            if (rand > 0.6) count = 2;
            if (rand > 0.75) count = 3;
            if (rand > 0.88) count = 4;
            if (rand > 0.95) count = 5;
            data[dateStr] = count;
        }
        // 确保今天和昨天有数据
        data['2026-01-17'] = 3;
        data['2026-01-16'] = 2;
        data['2026-01-15'] = 4;
        return data;
    })(),

    // 习惯养成
    habits: [
        {
            id: 'h1',
            name: '早起',
            description: '每天 7:00 前起床',
            color: '#009FAA',
            status: 'active',
            createdAt: '2026-01-01T00:00:00Z',
            records: (() => {
                const records = {};
                const today = new Date('2026-01-17');
                for (let i = 0; i < 30; i++) {
                    const d = new Date(today);
                    d.setDate(d.getDate() - i);
                    const dateStr = d.toISOString().split('T')[0];
                    // 最近15天基本打卡，再往前偶尔断
                    records[dateStr] = i < 15 ? true : (Math.random() > 0.3);
                }
                return records;
            })()
        },
        {
            id: 'h2',
            name: '喝水 2L',
            description: '每天喝水不少于 2000ml',
            color: '#3B82F6',
            status: 'active',
            createdAt: '2026-01-05T00:00:00Z',
            records: (() => {
                const records = {};
                const today = new Date('2026-01-17');
                for (let i = 0; i < 20; i++) {
                    const d = new Date(today);
                    d.setDate(d.getDate() - i);
                    const dateStr = d.toISOString().split('T')[0];
                    records[dateStr] = i < 10 ? true : (Math.random() > 0.4);
                }
                return records;
            })()
        },
        {
            id: 'h3',
            name: '冥想 10 分钟',
            description: '睡前冥想，放松身心',
            color: '#8B5CF6',
            status: 'active',
            createdAt: '2026-01-10T00:00:00Z',
            records: (() => {
                const records = {};
                const today = new Date('2026-01-17');
                for (let i = 0; i < 10; i++) {
                    const d = new Date(today);
                    d.setDate(d.getDate() - i);
                    const dateStr = d.toISOString().split('T')[0];
                    records[dateStr] = i < 5 ? true : (Math.random() > 0.5);
                }
                return records;
            })()
        },
        {
            id: 'h4',
            name: '读书 30 分钟',
            description: '每天睡前阅读至少30分钟',
            color: '#10B981',
            status: 'ended',
            createdAt: '2025-12-01T00:00:00Z',
            records: (() => {
                const records = {};
                const end = new Date('2026-01-05');
                for (let i = 0; i < 35; i++) {
                    const d = new Date(end);
                    d.setDate(d.getDate() - i);
                    const dateStr = d.toISOString().split('T')[0];
                    records[dateStr] = Math.random() > 0.2;
                }
                return records;
            })()
        }
    ],

    // 目标计划
    goals: [
        {
            id: 'g1',
            name: '自我提升·本周阅读计划',
            kind: 'goal',
            period: 'week',
            repeat: 'none',
            date: '2026-01-12',
            delayPolicy: 'default',
            delayCount: 0,
            relatedTaskIds: ['t1'],
            description: '本周完成《设计心理学》第三、四章阅读',
            standard: '每章输出至少3条读书笔记',
            status: 'pending',
            createdAt: '2026-01-12T08:00:00Z',
            updatedAt: '2026-01-12T08:00:00Z'
        },
        {
            id: 'g2',
            name: '健康计划·月跑量 100km',
            kind: 'goal',
            period: 'month',
            repeat: 'none',
            date: '2026-01-01',
            delayPolicy: 'default',
            delayCount: 0,
            relatedTaskIds: ['t2'],
            description: '通过每日晨跑积累月跑量',
            standard: '平均配速不低于 6:00/km',
            status: 'pending',
            createdAt: '2026-01-01T06:00:00Z',
            updatedAt: '2026-01-01T06:00:00Z'
        },
        {
            id: 'g3',
            name: '2026·掌握前端工程化',
            kind: 'goal',
            period: 'year',
            repeat: 'none',
            date: '2026-01-01',
            delayPolicy: 'default',
            delayCount: 0,
            relatedTaskIds: ['g1', 'g2'],
            description: '系统学习现代前端构建工具与架构设计',
            standard: '独立设计并实现一个完整工程化项目',
            status: 'pending',
            createdAt: '2026-01-01T00:00:00Z',
            updatedAt: '2026-01-01T00:00:00Z'
        },
        {
            id: 'g4',
            name: '工作效率·建立周报机制',
            kind: 'goal',
            period: 'month',
            repeat: 'none',
            date: '2026-01-01',
            delayPolicy: 'default',
            delayCount: 0,
            relatedTaskIds: ['t4'],
            description: '每周五固定输出高质量周报',
            standard: '覆盖所有项目进展，包含数据支撑',
            status: 'archived',
            createdAt: '2026-01-01T09:00:00Z',
            updatedAt: '2026-01-15T16:00:00Z'
        }
    ]
};
