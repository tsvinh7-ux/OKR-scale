/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { OkrAvatar, OkrProgressRing, OkrStatusChip, STATUS_COLORS } from "../components/okr_components";

const KPI_ICONS = {
    objectives: "fa-bullseye",
    key_results: "fa-key",
    progress: "fa-line-chart",
    on_track: "fa-check-circle",
    checkin_rate: "fa-calendar-check-o",
};

export class OkrDashboard extends Component {
    static template = "okr_scale.Dashboard";
    static components = { OkrAvatar, OkrProgressRing, OkrStatusChip };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null, ranking: null, cycleId: false, departmentId: false });
        onWillStart(() => this.load());
    }

    async load() {
        const kwargs = { cycle_id: this.state.cycleId || false, department_id: this.state.departmentId || false };
        const [data, ranking] = await Promise.all([
            this.orm.call("okr.scale.dashboard", "get_dashboard_data", [], kwargs),
            this.orm.call("okr.scale.dashboard", "get_ranking_data", [], kwargs),
        ]);
        this.state.data = data;
        this.state.ranking = ranking;
        this.state.cycleId = data.cycle ? data.cycle.id : false;
    }

    async onCycleChange(ev) {
        this.state.cycleId = parseInt(ev.target.value) || false;
        await this.load();
    }

    async onDepartmentChange(ev) {
        this.state.departmentId = parseInt(ev.target.value) || false;
        await this.load();
    }

    kpiIcon(kpi) {
        return kpi.icon || KPI_ICONS[kpi.key] || "fa-star";
    }

    get donut() {
        // Stacked donut segments of the objective statuses
        const total = this.state.data.status.reduce((sum, s) => sum + s.count, 0);
        const radius = 54;
        const circumference = 2 * Math.PI * radius;
        let offset = 0;
        const segments = [];
        for (const status of this.state.data.status) {
            if (!status.count) {
                continue;
            }
            const length = (status.count / total) * circumference;
            segments.push({ key: status.key, color: STATUS_COLORS[status.key], length, gap: circumference - length, offset: -offset });
            offset += length;
        }
        return { total, radius, segments };
    }

    statusColor(status) {
        return STATUS_COLORS[status] || "var(--okr-blue)";
    }

    objectiveDomain() {
        const domain = [["state", "in", ["running", "done"]]];
        if (this.state.cycleId) {
            domain.push(["cycle_id", "=", this.state.cycleId]);
        }
        if (this.state.departmentId) {
            domain.push(["department_id", "child_of", this.state.departmentId]);
        }
        return domain;
    }

    openObjectives(extraDomain = [], name = _t("Objectives")) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "okr.scale.objective",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [...this.objectiveDomain(), ...extraDomain],
        });
    }

    openRecord(model, id) {
        this.action.doAction({ type: "ir.actions.act_window", res_model: model, res_id: id, views: [[false, "form"]] });
    }

    openTree() {
        this.action.doAction("okr_scale.okr_objective_action_tree");
    }

    openRankings() {
        this.action.doAction("okr_scale.okr_ranking_action");
    }
}

registry.category("actions").add("okr_scale.dashboard", OkrDashboard);
