/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class OkrDashboard extends Component {
    static template = "okr_scale.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null, cycleId: false, departmentId: false, loading: true });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        const data = await this.orm.call("okr.scale.dashboard", "get_dashboard_data", [], {
            cycle_id: this.state.cycleId || false,
            department_id: this.state.departmentId || false,
        });
        this.state.data = data;
        this.state.cycleId = data.cycle ? data.cycle.id : false;
        this.state.loading = false;
    }

    async onCycleChange(ev) {
        this.state.cycleId = parseInt(ev.target.value) || false;
        await this.load();
    }

    async onDepartmentChange(ev) {
        this.state.departmentId = parseInt(ev.target.value) || false;
        await this.load();
    }

    get totalStatus() {
        return this.state.data.status.reduce((total, s) => total + s.count, 0);
    }

    statusPercent(status) {
        const total = this.totalStatus;
        return total ? (status.count * 100) / total : 0;
    }

    statusClass(status) {
        return {
            on_track: "bg-success",
            achieved: "bg-primary",
            at_risk: "bg-warning",
            off_track: "bg-danger",
        }[status] || "bg-secondary";
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
            views: [[false, "list"], [false, "form"]],
            domain: [...this.objectiveDomain(), ...extraDomain],
        });
    }

    openRecord(model, id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: id,
            views: [[false, "form"]],
        });
    }

    openTree() {
        this.action.doAction("okr_scale.okr_objective_action_tree");
    }
}

registry.category("actions").add("okr_scale.dashboard", OkrDashboard);
