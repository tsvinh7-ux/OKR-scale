/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { formatFloat } from "@web/core/utils/numbers";
import { OkrAvatar, OkrProgressRing, OkrStatusChip } from "@okr_scale/components/okr_components";

export const BAND_COLORS = {
    red: "var(--okr-danger)",
    yellow: "var(--okr-warning)",
    green: "var(--okr-success)",
};

/** Semicircle gauge of a 0.0 - 1.0 score, with the red / yellow / green bands. */
export class OkrScoreGauge extends Component {
    static template = "okr_scale_review.ScoreGauge";
    static props = {
        score: Number,
        band: { type: [String, Boolean], optional: true },
        width: { type: Number, optional: true },
        empty: { type: Boolean, optional: true },
    };
    static defaultProps = { width: 220 };

    get geometry() {
        const w = this.props.width;
        const stroke = Math.round(w / 13);
        const r = (w - stroke) / 2;
        const cx = w / 2;
        const cy = r + stroke / 2;
        return { w, h: cy + stroke / 2 + 2, stroke, r, cx, cy, path: `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}` };
    }
    get segments() {
        return [
            { key: "red", start: 0, len: 39.4 },
            { key: "yellow", start: 40, len: 29.4 },
            { key: "green", start: 70, len: 30 },
        ];
    }
    get value() {
        return Math.max(0, Math.min(1, this.props.score || 0)) * 100;
    }
    get color() {
        return BAND_COLORS[this.props.band] || "var(--okr-blue)";
    }
    /** Position of a marker at ``ratio`` (0..1) on the arc, for the 0.7 tick. */
    tick(ratio) {
        const g = this.geometry;
        const angle = Math.PI * (1 - ratio);
        const inner = g.r - g.stroke * 0.95;
        const outer = g.r + g.stroke * 0.95;
        return {
            x1: g.cx + inner * Math.cos(angle), y1: g.cy - inner * Math.sin(angle),
            x2: g.cx + outer * Math.cos(angle), y2: g.cy - outer * Math.sin(angle),
        };
    }
}

export class OkrCycleReview extends Component {
    static template = "okr_scale_review.CycleReview";
    static components = { OkrAvatar, OkrProgressRing, OkrStatusChip, OkrScoreGauge };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.router = useService("router");
        const action = this.props.action || {};
        const params = action.params || {};
        const context = action.context || {};
        const hash = (this.router.current && this.router.current.hash) || {};
        const cycleId = params.cycle_id || (context.active_model === "okr.scale.cycle" && context.active_id)
            || parseInt(hash.cycle_id) || false;
        this.state = useState({
            data: null,
            cycleId,
            departmentId: params.department_id || parseInt(hash.department_id) || false,
            selected: {},
            quotesExpanded: false,
            loading: false,
        });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        const data = await this.orm.call("okr.scale.review.board", "get_cycle_review_data", [], {
            cycle_id: this.state.cycleId || false,
            department_id: this.state.departmentId || false,
        });
        this.state.data = data;
        this.state.cycleId = data.cycle ? data.cycle.id : false;
        this.state.selected = {};
        this.state.loading = false;
        // Keep the filters in the URL so that a reload shows the same review
        this.router.pushState({
            cycle_id: this.state.cycleId || undefined,
            department_id: this.state.departmentId || undefined,
        });
    }

    // ------------------------------------------------------------------
    // Filters
    // ------------------------------------------------------------------
    async onCycleChange(ev) {
        this.state.cycleId = parseInt(ev.target.value) || false;
        await this.load();
    }

    async onDepartmentChange(ev) {
        this.state.departmentId = parseInt(ev.target.value) || false;
        await this.load();
    }

    // ------------------------------------------------------------------
    // Formatting
    // ------------------------------------------------------------------
    fmtScore(value) {
        return (value || 0).toFixed(2);
    }
    fmtPct(value) {
        return `${Math.round(value || 0)}%`;
    }
    fmtNumber(value) {
        const digits = Number.isInteger(value || 0) ? 0 : 2;
        return formatFloat(value || 0, { digits: [false, digits] });
    }
    bandColor(band) {
        return BAND_COLORS[band] || "var(--okr-line)";
    }
    bandWidth(bands, key) {
        const total = bands.red + bands.yellow + bands.green;
        return total ? (bands[key] * 100) / total : 0;
    }
    get scoreLabel() {
        return this.state.data.score_mode === "projected" ? _t("Projected score") : _t("Score");
    }
    get scoreHelp() {
        return this.state.data.score_mode === "projected"
            ? _t("Projected score = progress ÷ time elapsed, capped at 1.0: the score each objective is heading to at the current pace. Closed objectives keep their final grade.")
            : _t("Final grade of closed objectives, progress ÷ 100 for the others.");
    }
    get pace() {
        const data = this.state.data;
        return Math.round(data.overall.progress - data.cycle.elapsed);
    }

    // ------------------------------------------------------------------
    // Navigation
    // ------------------------------------------------------------------
    objectiveDomain() {
        const domain = [["state", "in", ["running", "done"]], ["cycle_id", "=", this.state.cycleId]];
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
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain: [...this.objectiveDomain(), ...extraDomain],
        });
    }

    openRecord(model, id) {
        this.action.doAction({ type: "ir.actions.act_window", res_model: model, res_id: id, views: [[false, "form"]] });
    }

    openReviews() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Reviews"),
            res_model: "okr.scale.review",
            views: [[false, "list"], [false, "form"]],
            domain: [["cycle_id", "=", this.state.cycleId]],
            context: { default_cycle_id: this.state.cycleId },
        });
    }

    async startReview(reviewType) {
        const action = await this.orm.call("okr.scale.review", "action_start_review", [
            this.state.cycleId, this.state.departmentId || false, reviewType || false,
        ]);
        await this.action.doAction(action);
    }

    // ------------------------------------------------------------------
    // Carry-over
    // ------------------------------------------------------------------
    get selectableKrs() {
        return this.state.data.carry_over.key_results.filter((kr) => kr.allowed && !kr.carried);
    }
    get selectedIds() {
        return Object.keys(this.state.selected).filter((id) => this.state.selected[id]).map((id) => parseInt(id));
    }
    get allSelected() {
        const krs = this.selectableKrs;
        return krs.length > 0 && krs.every((kr) => this.state.selected[kr.id]);
    }
    toggleKr(kr) {
        if (!kr.allowed || kr.carried) {
            return;
        }
        this.state.selected[kr.id] = !this.state.selected[kr.id];
    }
    toggleAll() {
        const value = !this.allSelected;
        for (const kr of this.selectableKrs) {
            this.state.selected[kr.id] = value;
        }
    }
    async carryOver() {
        const ids = this.selectedIds;
        if (!ids.length) {
            this.notification.add(_t("Select the key results to carry over first."), { type: "warning" });
            return;
        }
        const nextCycle = this.state.data.carry_over.next_cycle;
        await this.action.doAction("okr_scale_review.okr_carry_over_action", {
            additionalContext: {
                default_source_cycle_id: this.state.cycleId,
                default_target_cycle_id: nextCycle ? nextCycle.id : false,
                carry_kr_ids: ids,
            },
            onClose: () => this.load(),
        });
    }

    get visibleQuotes() {
        const quotes = this.state.data.quotes;
        return this.state.quotesExpanded ? quotes : quotes.slice(0, 6);
    }
}

registry.category("actions").add("okr_scale_review.cycle_review", OkrCycleReview);
