/** @odoo-module **/

import { Component } from "@odoo/owl";

export const STATUS_COLORS = {
    achieved: "var(--okr-navy)",
    on_track: "var(--okr-blue)",
    at_risk: "var(--okr-warning)",
    off_track: "var(--okr-danger)",
};

/** Circular progress indicator drawn in SVG. */
export class OkrProgressRing extends Component {
    static template = "okr_scale.ProgressRing";
    static props = {
        value: Number,
        size: { type: Number, optional: true },
        stroke: { type: Number, optional: true },
        status: { type: String, optional: true },
        light: { type: Boolean, optional: true },
    };
    static defaultProps = { size: 64, stroke: 6 };

    get radius() {
        return (this.props.size - this.props.stroke) / 2;
    }
    get circumference() {
        return 2 * Math.PI * this.radius;
    }
    get offset() {
        const value = Math.max(0, Math.min(100, this.props.value || 0));
        return this.circumference * (1 - value / 100);
    }
    get color() {
        if (this.props.light) {
            return "#FFFFFF";
        }
        return STATUS_COLORS[this.props.status] || "var(--okr-blue)";
    }
    get label() {
        return `${Math.round(this.props.value || 0)}%`;
    }
}

export class OkrAvatar extends Component {
    static template = "okr_scale.Avatar";
    static props = {
        userId: { type: [Number, Boolean], optional: true },
        name: { type: String, optional: true },
        size: { type: Number, optional: true },
        ring: { type: String, optional: true },
    };
    static defaultProps = { size: 32 };

    get src() {
        return this.props.userId ? `/web/image/res.users/${this.props.userId}/avatar_128` : "/base/static/img/avatar_grey.png";
    }
}

export class OkrStatusChip extends Component {
    static template = "okr_scale.StatusChip";
    static props = { status: { type: [String, Boolean], optional: true }, label: { type: String, optional: true } };
}
