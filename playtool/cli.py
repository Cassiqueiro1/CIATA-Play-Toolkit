from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from . import __version__
from .assets import PRESETS, convert, validate_kind
from .core import ToolError, load_config
from .release import inspect_release
from .manifest import build_manifest
from .googleplay import prepare, validate, commit, discard, remote_inventory
from .listing import (list_images, replace_images, get_listing_text, update_listing_text, get_app_details, update_app_details)

DEFAULT_CONFIG=Path('playtool.yaml'); DEFAULT_STATE=Path('.playtool-edit.json')
def emit(data, json_mode=False):
    if json_mode: print(json.dumps(data,ensure_ascii=False,indent=2)); return
    if isinstance(data,dict):
        for k,v in data.items(): print(f"{k}: {v}")
    else: print(data)

def cmd_init(args):
    path=Path(args.config)
    if path.exists() and not args.force: raise ToolError(f"Arquivo já existe: {path}. Use --force para substituir.")
    path.write_text("package: br.org.ciata.comunicaciata\ndefault_track: beta\nlanguage: pt-BR\nreview_url: https://ciata.org.br/comunica/play-review\n",encoding='utf-8')
    print(f"Configuração criada: {path.resolve()}")
def cmd_assets_convert(a): emit(convert(Path(a.input),Path(a.output),a.preset,a.mode,a.quality,a.background),a.json)
def cmd_assets_validate(a):
    result=validate_kind(Path(a.input),a.kind); emit(result,a.json)
    if not result['valid']: raise ToolError('Imagem reprovada: ' + '; '.join(result['errors']))
def cmd_release_inspect(a): emit(inspect_release(Path(a.aab),Path(a.mapping) if a.mapping else None,Path(a.symbols) if a.symbols else None),a.json)
def cmd_release_manifest(a):
    c=load_config(Path(a.config)); emit(build_manifest(c['package'],a.track or c['default_track'],a.name,Path(a.aab),Path(a.mapping) if a.mapping else None,Path(a.symbols) if a.symbols else None,a.notes,Path(a.output)),a.json)
def _state(path):
    p=Path(path)
    if not p.is_file(): raise ToolError(f"Estado não encontrado: {p}")
    return json.loads(p.read_text(encoding='utf-8'))
def cmd_play_prepare(a):
    c=load_config(Path(a.config)); result=prepare(c['package'],a.track or c['default_track'],Path(a.aab),a.name,a.notes,c['language'],Path(a.state),Path(a.mapping) if a.mapping else None,Path(a.symbols) if a.symbols else None); emit(result,a.json)
def cmd_play_inventory(a):
    c=load_config(Path(a.config)); emit(remote_inventory(c['package']),a.json)
def cmd_play_validate(a):
    s=_state(a.state); validate(s['package'],s['edit_id']); print('Edição validada. Ainda não confirmada.')
def cmd_play_discard(a):
    s=_state(a.state); discard(s['package'],s['edit_id']); Path(a.state).unlink(missing_ok=True); print('Edição descartada. Nenhuma alteração foi publicada.')
def cmd_play_commit(a):
    s=_state(a.state)
    phrase=f"PUBLICAR {s['package']} {s['version_code']} NA FAIXA {s['track']}"
    print('Confirmação de alto impacto. Digite exatamente:'); print(phrase)
    if input().strip()!=phrase: raise ToolError('Confirmação cancelada.')
    result=commit(s['package'],s['edit_id']); Path(a.state).unlink(missing_ok=True); print('Edição confirmada com sucesso.'); emit(result,a.json)
def cmd_listing_list(a):
    c=load_config(Path(a.config)); s=_state(a.state); emit(list_images(c['package'],s['edit_id'],a.language or c['language'],a.kind),a.json)
def cmd_listing_replace(a):
    c=load_config(Path(a.config)); s=_state(a.state); emit(replace_images(c['package'],s['edit_id'],a.language or c['language'],a.kind,[Path(p) for p in a.files]),a.json)
def cmd_listing_text_show(a):
    c=load_config(Path(a.config)); s=_state(a.state); emit(get_listing_text(c['package'],s['edit_id'],a.language or c['language']),a.json)
def cmd_listing_text_update(a):
    c=load_config(Path(a.config)); s=_state(a.state); emit(update_listing_text(c['package'],s['edit_id'],a.language or c['language'],title=a.title,title_file=Path(a.title_file) if a.title_file else None,short_description=a.short,short_file=Path(a.short_file) if a.short_file else None,full_description=a.full,full_file=Path(a.full_file) if a.full_file else None,video=a.video,clear_video=a.clear_video),a.json)
def cmd_listing_details_show(a):
    c=load_config(Path(a.config)); s=_state(a.state); emit(get_app_details(c['package'],s['edit_id']),a.json)
def cmd_listing_details_update(a):
    c=load_config(Path(a.config)); s=_state(a.state); emit(update_app_details(c['package'],s['edit_id'],a.default_language or c['language'],a.website,a.email,a.phone or ''),a.json)

def build_parser():
    p=argparse.ArgumentParser(prog='playtool',description='CIATA Play Publisher Toolkit, interface textual acessível.'); p.add_argument('--version',action='version',version=__version__)
    sp=p.add_subparsers(dest='command',required=True)
    x=sp.add_parser('init'); x.add_argument('--config',default=str(DEFAULT_CONFIG)); x.add_argument('--force',action='store_true'); x.set_defaults(func=cmd_init)
    assets=sp.add_parser('assets'); asp=assets.add_subparsers(dest='assets_command',required=True)
    x=asp.add_parser('convert'); x.add_argument('--input',required=True); x.add_argument('--output',required=True); x.add_argument('--preset',choices=PRESETS,required=True); x.add_argument('--mode',choices=['contain','cover','stretch'],default='contain'); x.add_argument('--quality',type=int,default=92); x.add_argument('--background',default='white'); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_assets_convert)
    x=asp.add_parser('validate'); x.add_argument('--input',required=True); x.add_argument('--kind',choices=['icon','feature','screenshot'],required=True); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_assets_validate)
    rel=sp.add_parser('release'); rsp=rel.add_subparsers(dest='release_command',required=True)
    x=rsp.add_parser('inspect'); x.add_argument('--aab',required=True); x.add_argument('--mapping'); x.add_argument('--symbols'); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_release_inspect)
    x=rsp.add_parser('manifest'); x.add_argument('--config',default=str(DEFAULT_CONFIG)); x.add_argument('--aab',required=True); x.add_argument('--name',required=True); x.add_argument('--notes',required=True); x.add_argument('--track'); x.add_argument('--mapping'); x.add_argument('--symbols'); x.add_argument('--output',default='release'); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_release_manifest)
    play=sp.add_parser('play'); psp=play.add_subparsers(dest='play_command',required=True)
    x=psp.add_parser('inventory'); x.add_argument('--config',default=str(DEFAULT_CONFIG)); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_play_inventory)
    x=psp.add_parser('prepare'); x.add_argument('--config',default=str(DEFAULT_CONFIG)); x.add_argument('--state',default=str(DEFAULT_STATE)); x.add_argument('--aab',required=True); x.add_argument('--name',required=True); x.add_argument('--notes',required=True); x.add_argument('--track'); x.add_argument('--mapping'); x.add_argument('--symbols'); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_play_prepare)
    x=psp.add_parser('validate'); x.add_argument('--state',default=str(DEFAULT_STATE)); x.set_defaults(func=cmd_play_validate)
    x=psp.add_parser('discard'); x.add_argument('--state',default=str(DEFAULT_STATE)); x.set_defaults(func=cmd_play_discard)
    x=psp.add_parser('commit'); x.add_argument('--state',default=str(DEFAULT_STATE)); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_play_commit)
    listing=sp.add_parser('listing'); lsp=listing.add_subparsers(dest='listing_command',required=True)
    x=lsp.add_parser('list'); x.add_argument('--config',default=str(DEFAULT_CONFIG)); x.add_argument('--state',default=str(DEFAULT_STATE)); x.add_argument('--language'); x.add_argument('--kind',choices=['icon','feature','screenshot'],required=True); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_listing_list)
    x=lsp.add_parser('replace'); x.add_argument('--config',default=str(DEFAULT_CONFIG)); x.add_argument('--state',default=str(DEFAULT_STATE)); x.add_argument('--language'); x.add_argument('--kind',choices=['icon','feature','screenshot'],required=True); x.add_argument('files',nargs='+'); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_listing_replace)
    x=lsp.add_parser('text-show'); x.add_argument('--config',default=str(DEFAULT_CONFIG)); x.add_argument('--state',default=str(DEFAULT_STATE)); x.add_argument('--language'); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_listing_text_show)
    x=lsp.add_parser('text-update'); x.add_argument('--config',default=str(DEFAULT_CONFIG)); x.add_argument('--state',default=str(DEFAULT_STATE)); x.add_argument('--language'); x.add_argument('--title'); x.add_argument('--title-file'); x.add_argument('--short'); x.add_argument('--short-file'); x.add_argument('--full'); x.add_argument('--full-file'); x.add_argument('--video'); x.add_argument('--clear-video',action='store_true'); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_listing_text_update)
    x=lsp.add_parser('details-show'); x.add_argument('--config',default=str(DEFAULT_CONFIG)); x.add_argument('--state',default=str(DEFAULT_STATE)); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_listing_details_show)
    x=lsp.add_parser('details-update'); x.add_argument('--config',default=str(DEFAULT_CONFIG)); x.add_argument('--state',default=str(DEFAULT_STATE)); x.add_argument('--default-language'); x.add_argument('--website',required=True); x.add_argument('--email',required=True); x.add_argument('--phone'); x.add_argument('--json',action='store_true'); x.set_defaults(func=cmd_listing_details_update)
    return p
def main():
    try:
        args=build_parser().parse_args(); args.func(args)
    except ToolError as e: print(f"Erro: {e}",file=sys.stderr); raise SystemExit(2)
    except KeyboardInterrupt: print('Operação cancelada pelo usuário.',file=sys.stderr); raise SystemExit(130)
if __name__=='__main__': main()
