/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { OkrAvatar, OkrProgressRing, OkrStatusChip } from "../components/okr_components";

export class OkrMyWorkspace extends Component {
    static template = "okr_scale.MyWorkspace";
    static components = { OkrAvatar, OkrProgressRing, OkrStatusChip };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.data = await this.orm.call("okr.scale.dashboard", "get_my_okr_data", []);
    }

    get greeting() {
        const hour = new Date().getHours();
        if (hour < 12) {
            return _t("Good morning");
        }
        return hour < 18 ? _t("Good afternoon") : _t("Good evening");
    }

    get firstName() {
        // Vietnamese names end with the given name
        const parts = (this.state.data.user.name || "").trim().split(/\s+/);
        return parts[parts.length - 1];
    }

    async checkin(kr) {
        await this.action.doAction(
            {
                type: "ir.actions.act_window",
                name: _t("Check-in"),
                res_model: "okr.scale.checkin",
                views: [[false, "form"]],
                target: "new",
                context: { default_key_result_id: kr.id },
            },
            { onClose: () => this.load() }
        );
    }

    newObjective() {
        this.action.doAction(
            {
                type: "ir.actions.act_window",
                name: _t("New Objective"),
                res_model: "okr.scale.objective",
                views: [[false, "form"]],
                context: { default_level: "individual" },
            },
            { onClose: () => this.load() }
        );
    }

    open(xmlid) {
        this.action.doAction(xmlid);
    }

    openRecord(model, id) {
        this.action.doAction({ type: "ir.actions.act_window", res_model: model, res_id: id, views: [[false, "form"]] });
    }
}

registry.category("actions").add("okr_scale.my_workspace", OkrMyWorkspace);
