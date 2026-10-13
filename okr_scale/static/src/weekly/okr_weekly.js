/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { OkrAvatar, OkrProgressRing, OkrStatusChip, okrFormatNumber } from "../components/okr_components";

const MOODS = [
    { key: "great", emoji: "🤩" },
    { key: "good", emoji: "🙂" },
    { key: "neutral", emoji: "😐" },
    { key: "struggling", emoji: "😣" },
];

export class OkrWeekly extends Component {
    static template = "okr_scale.Weekly";
    static components = { OkrAvatar, OkrProgressRing, OkrStatusChip };
    static props = ["*"];

    setup() {
        this.fmt = okrFormatNumber;
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.user = useService("user");
        this.moods = MOODS;
        this.confidences = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
        this.state = useState({
            tab: "mine",
            mine: null,
            team: null,
            isManager: false,
            lines: {},
            form: { summary: "", next_plan: "", help_needed: "", mood: "good" },
            saving: false,
            departmentId: false,
            expanded: {},
        });
        onWillStart(async () => {
            this.state.isManager = await this.user.hasGroup("okr_scale.group_okr_manager");
            await this.loadMine();
            if (this.state.isManager && !this.state.mine.key_results.length) {
                this.state.tab = "team";
            }
            if (this.state.isManager) {
                await this.loadTeam();
            }
        });
    }

    async loadMine() {
        const mine = await this.orm.call("okr.scale.weekly", "get_my_week", []);
        const lines = {};
        for (const kr of mine.key_results) {
            lines[kr.id] = { new_value: kr.boolean ? (kr.current >= 1 ? 1 : 0) : kr.current, confidence: parseInt(kr.confidence) || 7, note: "", blockers: "" };
        }
        this.state.lines = lines;
        if (mine.weekly) {
            Object.assign(this.state.form, mine.weekly);
        }
        this.state.mine = mine;
    }

    async loadTeam(week = false) {
        this.state.team = await this.orm.call("okr.scale.weekly", "get_team_week", [], {
            week_start: week || (this.state.team && this.state.team.week_start) || false,
            department_id: this.state.departmentId || false,
        });
    }

    get pending() {
        return this.state.mine.key_results.filter((kr) => !kr.done);
    }

    confidenceClass(value, selected) {
        const band = value <= 3 ? "low" : value <= 6 ? "mid" : "high";
        return `o_okr_conf o_okr_conf_${band} ${selected ? "active" : ""}`;
    }

    previewProgress(kr) {
        const line = this.state.lines[kr.id];
        if (!kr.manual) {
            return kr.progress;
        }
        if (kr.boolean) {
            return line.new_value >= 1 ? 100 : 0;
        }
        const span = kr.target - kr.start;
        if (!span) {
            return kr.progress;
        }
        return Math.max(0, Math.min(100, ((parseFloat(line.new_value || 0) - kr.start) * 100) / span));
    }

    async submit() {
        if (!this.state.form.next_plan.trim()) {
            this.notification.add(_t("Tell your team the plan for next week."), { type: "warning" });
            return;
        }
        this.state.saving = true;
        try {
            await this.orm.call("okr.scale.weekly", "submit_my_week", [{
                ...this.state.form,
                lines: this.pending.map((kr) => ({ key_result_id: kr.id, ...this.state.lines[kr.id] })),
            }]);
            this.notification.add(_t("Weekly check-in submitted. Have a great weekend!"), { type: "success" });
            await this.loadMine();
            if (this.state.isManager) {
                await this.loadTeam();
            }
        } finally {
            this.state.saving = false;
        }
    }

    async onDepartmentChange(ev) {
        this.state.departmentId = parseInt(ev.target.value) || false;
        await this.loadTeam();
    }

    async remind(row) {
        await this.orm.call("okr.scale.weekly", "remind_user", [row.user_id]);
        this.notification.add(_t("Reminder sent to %s", row.name), { type: "info" });
    }

    planOneOnOne(row) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "okr.scale.conversation",
            views: [[false, "form"]],
            context: { default_employee_user_id: row.user_id, default_manager_id: this.user.userId, default_cadence: "none" },
        });
    }

    toggle(row) {
        this.state.expanded[row.user_id] = !this.state.expanded[row.user_id];
    }

    moodEmoji(key) {
        const mood = MOODS.find((m) => m.key === key);
        return mood ? mood.emoji : "";
    }

    openKeyResult(id) {
        this.action.doAction({ type: "ir.actions.act_window", res_model: "okr.scale.key.result", res_id: id, views: [[false, "form"]] });
    }

    openWeekly(id) {
        this.action.doAction({ type: "ir.actions.act_window", res_model: "okr.scale.weekly", res_id: id, views: [[false, "form"]] });
    }
}

registry.category("actions").add("okr_scale.weekly", OkrWeekly);
