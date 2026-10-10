/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { OkrAvatar, OkrProgressRing, OkrStatusChip } from "../components/okr_components";

const PODIUM_RINGS = { 1: "gold", 2: "silver", 3: "bronze" };

export class OkrRankings extends Component {
    static template = "okr_scale.Rankings";
    static components = { OkrAvatar, OkrProgressRing, OkrStatusChip };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null, tab: "people", cycleId: false, departmentId: false });
        onWillStart(() => this.load());
    }

    async load() {
        const data = await this.orm.call("okr.scale.dashboard", "get_ranking_data", [], {
            cycle_id: this.state.cycleId || false,
            department_id: this.state.departmentId || false,
        });
        this.state.data = data;
        this.state.cycleId = data.cycle ? data.cycle.id : false;
    }

    get tabs() {
        const tabs = [
            { key: "people", label: _t("People"), icon: "fa-user" },
            { key: "departments", label: _t("Departments"), icon: "fa-building" },
            { key: "objectives", label: _t("Objectives"), icon: "fa-bullseye" },
            { key: "key_results", label: _t("Key Results"), icon: "fa-key" },
        ];
        for (const board of this.state.data.extra_boards) {
            tabs.push({ key: board.key, label: board.title, icon: board.icon || "fa-star" });
        }
        return tabs;
    }

    get extraBoard() {
        return this.state.data.extra_boards.find((b) => b.key === this.state.tab);
    }

    /** Top 3 displayed as a podium: 2nd, 1st, 3rd. */
    podium(rows) {
        const [first, second, third] = rows;
        return [second, first, third].filter(Boolean);
    }

    ring(rank) {
        return PODIUM_RINGS[rank] || "";
    }

    async onCycleChange(ev) {
        this.state.cycleId = parseInt(ev.target.value) || false;
        await this.load();
    }

    async onDepartmentChange(ev) {
        this.state.departmentId = parseInt(ev.target.value) || false;
        await this.load();
    }

    openRecord(model, id) {
        this.action.doAction({ type: "ir.actions.act_window", res_model: model, res_id: id, views: [[false, "form"]] });
    }
}

registry.category("actions").add("okr_scale.rankings", OkrRankings);
