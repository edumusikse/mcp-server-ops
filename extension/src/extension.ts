import * as vscode from 'vscode';
import { OpsPanel } from './OpsPanel';

export function activate(ctx: vscode.ExtensionContext) {
    ctx.subscriptions.push(
        vscode.window.registerWebviewViewProvider(OpsPanel.viewId, new OpsPanel(ctx), {
            webviewOptions: { retainContextWhenHidden: true },
        })
    );
}

export function deactivate() {}
