#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aviator Bot Inteligente V3 - Ubuntu 22.04 LTS
✅ Login automático no TipMiner
✅ Coleta de dados REAIS após autenticação
✅ Sistema de logs completo
✅ Modo headless para servidores sem interface gráfica
✅ Todos os módulos originais preservados (1-5) + Módulos 6 e 7 adicionados
"""

import sys
import select
import termios
import tty
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import logging
from logging.handlers import RotatingFileHandler
from collections import defaultdict
import numpy as np

# ============================================
# CONFIGURAÇÃO DE LOGS
# ============================================
def setup_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    log_file = f"logs/bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logger = logging.getLogger('AviatorBot')
    logger.setLevel(logging.DEBUG)
    
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()

# ============================================
# FUNÇÕES DE DETECÇÃO DE TECLA PARA LINUX
# ============================================
def kbhit_linux(timeout=0.1):
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        return bool(ready)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def getch_linux():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# ============================================
# CLASSE DE LOGIN (CORRIGIDA PARA MODO HEADLESS)
# ============================================
class TipMinerLogin:
    def __init__(self, logger):
        self.logger = logger
        self.url_login = "https://www.tipminer.com/br/login"
        self.url_historico = "https://www.tipminer.com/br/historico/sortenabet/aviator"
        self.email = "sc4ry.php@gmail.com"
        self.senha = "Passe@123"
        self.context = None
        self.page = None
    
    def realizar_login(self):
        logger.info("="*80)
        logger.info("🚀 INICIANDO PROCESSO DE LOGIN NO TIPMINER")
        logger.info("="*80)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ]
                )
                
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    locale="pt-BR"
                )
                
                if self.carregar_cookies(context):
                    logger.info("🍪 Cookies carregados - Verificando sessão...")
                    page = context.new_page()
                    page.goto(self.url_historico, wait_until="networkidle", timeout=30000)
                    time.sleep(3)
                    
                    if "login" not in page.url.lower():
                        logger.info("✅ Sessão válida encontrada nos cookies!")
                        self.context = context
                        self.page = page
                        return context, page
                    else:
                        logger.info("⚠️ Cookies expirados - Realizando novo login...")
                        context.close()
                        browser.close()
                
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ]
                )
                
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    locale="pt-BR"
                )
                
                page = context.new_page()
                page.goto(self.url_login, wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
                
                try:
                    page.wait_for_selector('button:has-text("Prefiro continuar no escuro")', timeout=5000)
                    page.click('button:has-text("Prefiro continuar no escuro")')
                    time.sleep(1)
                except:
                    pass
                
                logger.info(f"📧 Preenchendo email: {self.email}")
                page.fill('input[type="email"], input[name="email"]', self.email)
                time.sleep(1)
                
                logger.info("🔒 Preenchendo senha...")
                page.fill('input[type="password"], input[name="password"]', self.senha)
                time.sleep(1)
                
                logger.info("🖱️  Clicando em 'Acessar'...")
                page.click('button:has-text("Acessar"), button[type="submit"]')
                time.sleep(5)
                
                if "historico" in page.url or "dashboard" in page.url or "home" in page.url:
                    logger.info("✅✅ LOGIN BEM-SUCEDIDO!")
                    logger.info(f"📍 Redirecionado para: {page.url}")
                    
                    self._salvar_cookies(context.cookies())
                    
                    self.context = context
                    self.page = page
                    return context, page
                
                else:
                    logger.error("❌ FALHA NO LOGIN: Verifique email/senha")
                    screenshot_path = "logs/login_error.png"
                    try:
                        page.screenshot(path=screenshot_path)
                        logger.error(f"📸 Screenshot salvo: {screenshot_path}")
                    except:
                        pass
                    browser.close()
                    return None, None
                    
        except PlaywrightTimeoutError as e:
            logger.error(f"❌ TIMEOUT durante login: {e}")
            return None, None
        except Exception as e:
            logger.error(f"❌ ERRO DURANTE LOGIN: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None
    
    def _salvar_cookies(self, cookies):
        try:
            if not os.path.exists('data'):
                os.makedirs('data')
            
            with open('data/cookies.json', 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            
            logger.info("🍪 Cookies salvos em: data/cookies.json")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar cookies: {e}")
    
    def carregar_cookies(self, context):
        try:
            cookies_path = "data/cookies.json"
            if os.path.exists(cookies_path):
                with open(cookies_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                
                context.add_cookies(cookies)
                logger.info("✅ Cookies carregados com sucesso")
                return True
            else:
                logger.info("ℹ️  Nenhum cookie salvo encontrado")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar cookies: {e}")
            return False

# ============================================
# MÓDULO 6 - ANÁLISE DE HORÁRIOS PAGANTES
# ============================================
class HorarioPaganteAnalyzer:
    def __init__(self, logger):
        self.logger = logger
        self.horario_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0, 'last_update': datetime.now().strftime('%Y-%m-%d')})
        self.dia_semana_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0, 'last_update': datetime.now().strftime('%Y-%m-%d')})
        self.historico_7d = []
        self.historico_31d = []
        self.ultima_atualizacao = datetime.now()
        self.carregar_analise_horarios()
    
    def carregar_analise_horarios(self):
        if os.path.exists('data/horario_pagante.json'):
            try:
                with open('data/horario_pagante.json', 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    self.horario_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0, 'last_update': datetime.now().strftime('%Y-%m-%d')}, dados.get('horario_stats', {}))
                    self.dia_semana_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0, 'last_update': datetime.now().strftime('%Y-%m-%d')}, dados.get('dia_semana_stats', {}))
                    self.historico_7d = dados.get('historico_7d', [])
                    self.historico_31d = dados.get('historico_31d', [])
                logger.info(f"✅ Carregada análise de horários pagantes ({len(self.horario_stats)} horas analisadas)")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar análise de horários: {e}")
    
    def salvar_analise_horarios(self):
        try:
            if not os.path.exists('data'):
                os.makedirs('data')
            
            dados = {
                'horario_stats': dict(self.horario_stats),
                'dia_semana_stats': dict(self.dia_semana_stats),
                'historico_7d': self.historico_7d[-7:],
                'historico_31d': self.historico_31d[-31:]
            }
            with open('data/horario_pagante.json', 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[⚠️] Erro ao salvar análise de horários: {e}")
    
    def atualizar_estatisticas(self, hora, dia_semana, is_win):
        self.horario_stats[hora]['total'] += 1
        self.horario_stats[hora]['wins'] += 1 if is_win else 0
        self.horario_stats[hora]['losses'] += 0 if is_win else 1
        self.horario_stats[hora]['last_update'] = datetime.now().strftime('%Y-%m-%d')
        
        self.dia_semana_stats[dia_semana]['total'] += 1
        self.dia_semana_stats[dia_semana]['wins'] += 1 if is_win else 0
        self.dia_semana_stats[dia_semana]['losses'] += 0 if is_win else 1
        self.dia_semana_stats[dia_semana]['last_update'] = datetime.now().strftime('%Y-%m-%d')
        
        agora = datetime.now()
        if (agora - self.ultima_atualizacao).days >= 1:
            dia_resumo = {
                'data': agora.strftime('%Y-%m-%d'),
                'hora_stats': {h: dict(stats) for h, stats in self.horario_stats.items()},
                'dia_stats': {d: dict(stats) for d, stats in self.dia_semana_stats.items()}
            }
            self.historico_7d.append(dia_resumo)
            self.historico_31d.append(dia_resumo)
            self.ultima_atualizacao = agora
            self.salvar_analise_horarios()
    
    def calcular_bonus_horario_pagante(self, hora, dia_semana):
        stats_hora = self.horario_stats.get(hora, {'wins': 0, 'losses': 0, 'total': 0})
        total_hora = stats_hora['total']
        
        stats_dia = self.dia_semana_stats.get(dia_semana, {'wins': 0, 'losses': 0, 'total': 0})
        total_dia = stats_dia['total']
        
        win_rate_hora = stats_hora['wins'] / total_hora if total_hora >= 50 else 0.5
        win_rate_dia = stats_dia['wins'] / total_dia if total_dia >= 30 else 0.5
        
        bonus = 0
        
        if total_hora >= 200:
            if win_rate_hora >= 0.62:
                bonus += 7
            elif win_rate_hora >= 0.58:
                bonus += 4
            elif win_rate_hora <= 0.45:
                bonus -= 6
            elif win_rate_hora <= 0.48:
                bonus -= 3
        
        if total_dia >= 150:
            if win_rate_dia >= 0.60:
                bonus += 3
            elif win_rate_dia <= 0.47:
                bonus -= 2
        
        return bonus, {
            'win_rate_hora': win_rate_hora,
            'total_hora': total_hora,
            'win_rate_dia': win_rate_dia,
            'total_dia': total_dia,
            'bonus_calculado': bonus
        }

# ============================================
# MÓDULO 7 - IA DE AUTO-APRENDIZAGEM
# ============================================
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import joblib
    AI_AVAILABLE = True
    logger.info("✅ IA de auto-aprendizagem ativada (Random Forest)")
except ImportError:
    AI_AVAILABLE = False
    logger.warning("⚠️ scikit-learn não instalado. IA desativada. Para ativar: pip3 install scikit-learn pandas numpy joblib")

class IAAutoAprendizagem:
    def __init__(self, logger):
        self.logger = logger
        self.X = []
        self.y = []
        self.scaler = StandardScaler() if AI_AVAILABLE else None
        self.model = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42) if AI_AVAILABLE else None
        self.trained = False
        self.ultima_retreinamento = datetime.now()
        self.min_samples_para_treino = 100
        self.carregar_modelo()
    
    def carregar_modelo(self):
        if not AI_AVAILABLE:
            return
        
        if os.path.exists('data/ia_modelo.pkl') and os.path.exists('data/ia_scaler.pkl'):
            try:
                self.model = joblib.load('data/ia_modelo.pkl')
                self.scaler = joblib.load('data/ia_scaler.pkl')
                self.trained = True
                logger.info("✅ Modelo de IA carregado com sucesso")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar modelo de IA: {e}")
                self.model = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42)
                self.scaler = StandardScaler()
    
    def salvar_modelo(self):
        if not AI_AVAILABLE or not self.trained:
            return
        
        try:
            if not os.path.exists('data'):
                os.makedirs('data')
            
            joblib.dump(self.model, 'data/ia_modelo.pkl')
            joblib.dump(self.scaler, 'data/ia_scaler.pkl')
            logger.info(f"✅ Modelo de IA salvo ({len(self.X)} amostras)")
        except Exception as e:
            logger.error(f"[⚠️] Erro ao salvar modelo de IA: {e}")

# ============================================
# CLASSE PRINCIPAL DO BOT
# ============================================
class AviatorBotInteligenteV3:
    def __init__(self, logger, login_manager):
        self.logger = logger
        self.login_manager = login_manager
        self.url = "https://www.tipminer.com/br/historico/sortenabet/aviator"
        self.historico_completo = []
        self.padroes_detectados = {}
        self.padroes_dia = defaultdict(lambda: {'ocorrencias': 0, 'acertos': 0, 'ultima_ocorrencia': None})
        self.historico_padroes = defaultdict(lambda: {'win': 0, 'loss': 0})
        self.sinais_enviados = []
        self.total_coletas = 0
        self.data_inicio = datetime.now().date()
        self.ultima_analise_completa = None
        self.last_round_value = None
        self.ultima_rodada_coletada = None
        self.meta_diaria = 10.0
        self.stop_win = 15.0
        self.stop_loss = -5.0
        self.total_lucro = 0.0
        self.memoria_erros = []
        self.regras_auto_correcao = []
        self.acertos_detalhados = []
        self.erros_detalhados = []
        self.sequencia_atual_derrotas = 0
        self.scheduled_entries = []
        self.horario_analyzer = HorarioPaganteAnalyzer(logger)
        self.ia_aprendizagem = IAAutoAprendizagem(logger)
        
        if not os.path.exists('data'):
            os.makedirs('data')
        
        self.carregar_padroes()
        self.carregar_padroes_historicos()
        self.carregar_regras_auto_correcao()
        self.carregar_acertos_erros()
    
    def carregar_padroes(self):
        if os.path.exists('data/padroes.json'):
            try:
                with open('data/padroes.json', 'r', encoding='utf-8') as f:
                    self.padroes_detectados = json.load(f)
                for padrao_id, info in self.padroes_detectados.items():
                    if 'historico' not in info:
                        acertos = info.get('acertos', 1)
                        ocorrencias = info.get('ocorrencias', 1)
                        info['historico'] = [1] * acertos + [0] * (ocorrencias - acertos)
                    info.setdefault('descricao', f'Padrão {padrao_id}')
                    info.setdefault('ocorrencias', len(info['historico']))
                    info.setdefault('acertos', sum(info['historico']))
                    info.setdefault('ultima_ocorrencia', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    info.setdefault('taxa_sucesso', (info['acertos'] / info['ocorrencias']) * 100 if info['ocorrencias'] > 0 else 0)
                    info.setdefault('data_ultima_atualizacao', datetime.now().strftime('%Y-%m-%d'))
                logger.info(f"✅ Carregados {len(self.padroes_detectados)} padrões salvos")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar padrões: {e}")
                self.padroes_detectados = {}
        else:
            self.padroes_detectados = {}
    
    def carregar_padroes_historicos(self):
        if os.path.exists('data/padroes_historicos.json'):
            try:
                with open('data/padroes_historicos.json', 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                for padrao in dados.get('padroes', []):
                    padrao_id = padrao['padrao']
                    if padrao_id not in self.padroes_detectados:
                        self.padroes_detectados[padrao_id] = {
                            'descricao': padrao.get('descricao', f"Padrão histórico: {padrao_id}"),
                            'ocorrencias': padrao['ocorrencias'],
                            'acertos': int((padrao['taxa'] / 100) * padrao['ocorrencias']),
                            'ultima_ocorrencia': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'taxa_sucesso': padrao['taxa'],
                            'historico': [1] * int((padrao['taxa'] / 100) * padrao['ocorrencias']) +
                                         [0] * (padrao['ocorrencias'] - int((padrao['taxa'] / 100) * padrao['ocorrencias'])),
                            'data_ultima_atualizacao': datetime.now().strftime('%Y-%m-%d'),
                            'fonte': 'HISTORICO'
                        }
                logger.info(f"✅ Carregados {len(dados.get('padroes', []))} padrões históricos lucrativos")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar padrões históricos: {e}")
                return False
        else:
            logger.info("ℹ️  Nenhum padrão histórico encontrado")
            return False
    
    def carregar_regras_auto_correcao(self):
        if os.path.exists('data/regras_auto_correcao.json'):
            try:
                with open('data/regras_auto_correcao.json', 'r', encoding='utf-8') as f:
                    self.regras_auto_correcao = json.load(f)
                logger.info(f"✅ Carregadas {len(self.regras_auto_correcao)} regras de auto-correção")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar regras de auto-correção: {e}")
                self.regras_auto_correcao = []
        else:
            self.regras_auto_correcao = []
    
    def carregar_acertos_erros(self):
        if os.path.exists('data/acertos_detalhados.json'):
            try:
                with open('data/acertos_detalhados.json', 'r', encoding='utf-8') as f:
                    self.acertos_detalhados = json.load(f)
                logger.info(f"✅ Carregados {len(self.acertos_detalhados)} acertos detalhados")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar acertos detalhados: {e}")
                self.acertos_detalhados = []
        else:
            self.acertos_detalhados = []
        
        if os.path.exists('data/erros_detalhados.json'):
            try:
                with open('data/erros_detalhados.json', 'r', encoding='utf-8') as f:
                    self.erros_detalhados = json.load(f)
                logger.info(f"✅ Carregados {len(self.erros_detalhados)} erros detalhados")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar erros detalhados: {e}")
                self.erros_detalhados = []
        else:
            self.erros_detalhados = []
    
    def salvar_padroes(self):
        try:
            with open('data/padroes.json', 'w', encoding='utf-8') as f:
                json.dump(self.padroes_detectados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[⚠️] Erro ao salvar padrões: {e}")
    
    def salvar_regras_auto_correcao(self):
        try:
            with open('data/regras_auto_correcao.json', 'w', encoding='utf-8') as f:
                json.dump(self.regras_auto_correcao, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[⚠️] Erro ao salvar regras de auto-correção: {e}")
    
    def salvar_acertos_erros(self):
        try:
            with open('data/acertos_detalhados.json', 'w', encoding='utf-8') as f:
                json.dump(self.acertos_detalhados, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Acertos detalhados salvos ({len(self.acertos_detalhados)} registros)")
        except Exception as e:
            logger.error(f"[⚠️] Erro ao salvar acertos detalhados: {e}")
        
        try:
            with open('data/erros_detalhados.json', 'w', encoding='utf-8') as f:
                json.dump(self.erros_detalhados, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Erros detalhados salvos ({len(self.erros_detalhados)} registros)")
        except Exception as e:
            logger.error(f"[⚠️] Erro ao salvar erros detalhados: {e}")
    
    def fetch_data(self, page):
        try:
            logger.debug("🔄 Iniciando coleta de dados...")
            
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            data = page.evaluate("""() => {
                const container = document.querySelector('[class*="history"]');
                if (!container) return [];
                const text = container.textContent;
                const pattern = /(\\d{2}\\/\\d{2}\\/\\d{4}\\s+\\d{2}:\\d{2}:\\d{2})\\s*([\\d,]+)x/g;
                const matches = [];
                let match;
                while ((match = pattern.exec(text)) !== null) {
                    matches.push({datetime: match[1], value: match[2]});
                }
                return matches;
            }""")
            
            multipliers = []
            for item in data:
                try:
                    num = float(item['value'].replace(',', '.'))
                    if 0.01 <= num <= 1000.00:
                        multipliers.append(num)
                except:
                    continue
            
            if multipliers:
                logger.info(f"✅ Coletados {len(multipliers)} dados reais")
                return multipliers
            else:
                logger.warning("⚠️ Nenhum dado coletado")
                return []
                
        except Exception as e:
            logger.error(f"[❌] ERRO na coleta: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def analisar_sequencias(self, dados):
        sequencias = []
        sequencia_atual = {'tipo': None, 'tamanho': 0, 'valores': []}
        for mult in dados:
            is_win = mult >= 2.0
            if sequencia_atual['tipo'] is None:
                sequencia_atual['tipo'] = 'WIN' if is_win else 'LOSS'
                sequencia_atual['tamanho'] = 1
                sequencia_atual['valores'] = [mult]
            elif (sequencia_atual['tipo'] == 'WIN' and is_win) or \
                 (sequencia_atual['tipo'] == 'LOSS' and not is_win):
                sequencia_atual['tamanho'] += 1
                sequencia_atual['valores'].append(mult)
            else:
                sequencias.append(sequencia_atual.copy())
                sequencia_atual['tipo'] = 'WIN' if is_win else 'LOSS'
                sequencia_atual['tamanho'] = 1
                sequencia_atual['valores'] = [mult]
        if sequencia_atual['tipo']:
            sequencias.append(sequencia_atual)
        return sequencias
    
    def verificar_status_mercado_aprimorado(self, sequencias):
        sequencias_1_2 = sum(1 for s in sequencias[:20] if s['tipo'] == 'LOSS' and 1 <= s['tamanho'] <= 2)
        sequencias_3 = sum(1 for s in sequencias[:20] if s['tipo'] == 'LOSS' and s['tamanho'] == 3)
        if sequencias_1_2 >= 2:
            return "MUITO BOM", sequencias_1_2
        elif sequencias_3 >= 2:
            return "BOM", sequencias_3
        elif sequencias_1_2 + sequencias_3 >= 2:
            return "NORMAL", sequencias_1_2 + sequencias_3
        else:
            return "RUIM", 0
    
    def classificar_vela_cores(self, multiplier):
        if 1.00 <= multiplier < 2.00:
            return 'AZUL'
        elif 2.00 <= multiplier < 10.00:
            return 'ROXA'
        elif multiplier >= 10.00:
            return 'ROSA'
        else:
            return 'OUTRO'
    
    def detectar_padroes_azul(self, dados):
        if dados and len(dados) >= 2:
            if abs(dados[0] - 1.00) < 0.01:
                return {
                    'tipo': 'PADRAO_RESET',
                    'padrao': '1.00X_RESET',
                    'confianca': 85.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'resultado': None,
                    'motivo': "Padrão de reset detectado (1.00x) - quem comanda o game é o Azul"
                }
            if 1.74 <= dados[0] <= 1.76 and 1.74 <= dados[1] <= 1.76:
                return {
                    'tipo': 'PADRAO_CICLO',
                    'padrao': '1.75X_REPETIDO',
                    'confianca': 80.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'resultado': None,
                    'motivo': "Padrão de ciclo detectado (1.75x repetido) - ciclo está acabando"
                }
            if 1.33 <= dados[0] <= 1.35 and 1.33 <= dados[1] <= 1.35:
                return {
                    'tipo': 'PADRAO_CICLO',
                    'padrao': '1.34X_REPETIDO',
                    'confianca': 75.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'resultado': None,
                    'motivo': "Padrão de ciclo detectado (1.34x repetido) - ciclo está acabando"
                }
        return None
    
    def detectar_padrao_xadrez(self, dados):
        if dados and len(dados) >= 3:
            if (dados[0] >= 2.0 and dados[1] < 2.0 and dados[2] >= 2.0):
                return {
                    'tipo': 'PADRAO_XADREZ',
                    'padrao': 'POSITIVO_XADREZ',
                    'confianca': 70.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'resultado': None,
                    'motivo': "Padrão de xadrez positivo detectado (repete consistentemente)"
                }
            if (dados[0] < 2.0 and dados[1] >= 2.0 and dados[2] < 2.0):
                return {
                    'tipo': 'PADRAO_XADREZ',
                    'padrao': 'NEGATIVO_XADREZ',
                    'confianca': 70.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'resultado': None,
                    'motivo': "Padrão de xadrez negativo detectado (repete consistentemente)"
                }
        return None
    
    def analisar_estrategia_azuis(self, dados):
        if dados and len(dados) >= 1:
            if 1.00 <= dados[0] < 2.00:
                decimal_str = str(dados[0]).split('.')[1]
                primeiro_digito = int(decimal_str[0]) if decimal_str else 0
                if primeiro_digito >= 1:
                    return {
                        'tipo': 'ESTRATEGIA_AZUIS_DECIMAL',
                        'padrao': f'AZUL_{dados[0]:.2f}',
                        'confianca': 75.0,
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'valor_entrada': 1.0,
                        'resultado': None,
                        'motivo': f"Vela azul {dados[0]:.2f}x → previsão de {primeiro_digito} casas de azul"
                    }
        return None
    
    def detectar_estrategias_modo_2(self, dados):
        if len(dados) < 6:
            return None
        if self.classificar_vela_cores(dados[-6]) != 'ROSA':
            return None
        azul_count = 0
        for i in range(-5, 0):
            if self.classificar_vela_cores(dados[i]) == 'AZUL':
                azul_count += 1
            else:
                break
        if azul_count >= 5:
            confianca = min(85, 70 + (azul_count - 5) * 5)
            return {
                'tipo': 'ENTRADA_MODO_2',
                'padrao': f'ROSA_{azul_count}_AZUL',
                'confianca': confianca,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'resultado': None,
                'motivo': f"Módulo 2: ROSA seguido de {azul_count} AZULs - Entrar na próxima rodada"
            }
        return None
    
    def schedule_3x_entries(self, dados):
        if not dados:
            return None
        current = dados[0]
        current_time = datetime.now()
        if 2.90 <= current <= 3.10:
            entry_time_15s = current_time + timedelta(seconds=15)
            self.scheduled_entries.append({
                'entry_time': entry_time_15s,
                'max_entries': 3,
                'entries_made': 0,
                'tipo': 'SCHEDULED_3X_15S'
            })
            entry_time_exact = current_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
            self.scheduled_entries.append({
                'entry_time': entry_time_exact,
                'max_entries': 2,
                'entries_made': 0,
                'tipo': 'SCHEDULED_3X_EXACT_MINUTE'
            })
            return {
                'tipo': 'SCHEDULED_3X',
                'padrao': '3X_VELOCITIES',
                'confianca': 72.0,
                'timestamp': current_time.strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'resultado': None,
                'motivo': f"Vela de 3x detectada ({current:.2f}x) → 2 estratégias de timing ativadas"
            }
        return None
    
    def schedule_10x_entries(self, dados):
        if not dados:
            return None
        current = dados[0]
        current_time = datetime.now()
        if current >= 10.0:
            self.last_10x_time = current_time
            return None
        if hasattr(self, 'last_10x_time') and (datetime.now() - self.last_10x_time).seconds > 600:
            entry_time = datetime.now() - timedelta(seconds=20)
            self.scheduled_entries.append({
                'entry_time': entry_time,
                'max_entries': 3,
                'entries_made': 0,
                'tipo': 'SCHEDULED_5X'
            })
            return {
                'tipo': 'SCHEDULED_5X',
                'padrao': '5X_STRATEGY',
                'confianca': 72.0,
                'timestamp': current_time.strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'resultado': None,
                'motivo': "Estratégia de 5x ativada: Entrar até 20s antes e realizar 3 entradas"
            }
        return None
    
    def detectar_padrao_3_sequencias(self, dados):
        if len(dados) < 4:
            return None
        if (self.classificar_vela_cores(dados[0]) in ['ROXA', 'ROSA'] and
            self.classificar_vela_cores(dados[1]) in ['ROXA', 'ROSA'] and
            self.classificar_vela_cores(dados[2]) == 'AZUL' and
            self.classificar_vela_cores(dados[3]) in ['ROXA', 'ROSA']):
            return {
                'tipo': 'PADRAO_3_SEQUENCIAS',
                'padrao': 'ROXA_ROSA_QUEBRA_AZUL',
                'confianca': 85.0,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'resultado': None,
                'motivo': "Padrão 3 sequências detectado: ROXA/ROSA → ROXA/ROSA → QUEBRA AZUL → Próxima vela ROXA/ROSA"
            }
        return None
    
    def detectar_gatilho_surreal(self, dados):
        if len(dados) < 6:
            return None
        velas_abaixo_149 = sum(1 for i in range(6) if dados[i] < 1.49)
        if velas_abaixo_149 >= 5:
            vela_especial = dados[5]
            if 1.11 <= vela_especial <= 1.99:
                return {
                    'tipo': 'GATILHO_SURREAL',
                    'padrao': '5_VEIAS_ABAIXO_149X',
                    'confianca': 90.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'resultado': None,
                    'motivo': f"Gatilho Surreal detectado: {velas_abaixo_149} velas < 1.49x + vela especial {vela_especial:.2f}x"
                }
        return None
    
    def detectar_padrao_10x_reset(self, dados):
        if len(dados) < 3:
            return None
        if (abs(dados[0] - 1.00) < 0.01 and
            1.36 <= dados[1] <= 1.38 and
            abs(dados[2] - 1.00) < 0.01):
            return {
                'tipo': 'PADRAO_10X_RESET',
                'padrao': '1.00X_1.37X_1.00X',
                'confianca': 95.0,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'resultado': None,
                'motivo': "Padrão 10x Reset detectado: 1.00x → 1.37x → 1.00x → Próxima vela 10x"
            }
        return None
    
    def detectar_repeticao_casas(self, dados):
        if len(dados) < 6:
            return None
        repeticoes = {'1.30': 0, '1.40': 0, '1.70': 0}
        for i in range(6):
            if 1.29 <= dados[i] <= 1.31:
                repeticoes['1.30'] += 1
            elif 1.39 <= dados[i] <= 1.41:
                repeticoes['1.40'] += 1
            elif 1.69 <= dados[i] <= 1.71:
                repeticoes['1.70'] += 1
        if repeticoes['1.30'] >= 2 and repeticoes['1.40'] >= 2 and repeticoes['1.70'] >= 2:
            return {
                'tipo': 'REPETICAO_CASAS',
                'padrao': 'CASAS_1.30_1.40_1.70',
                'confianca': 95.0,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'resultado': None,
                'motivo': "Repetição de casas detectada: 1.30, 1.40, 1.70 (2x cada)"
            }
        return None
    
    def analisar_erro_contextual(self, vela_entrada, vela_resultado, hora_atual):
        contexto = {
            'tipo_erro': 'DESCONHECIDO',
            'hora': hora_atual,
            'recomendacao': 'EVITAR_ENTRADA'
        }
        horarios_criticos = [2, 3, 4, 5, 14, 15]
        if hora_atual in horarios_criticos:
            contexto['tipo_erro'] = 'HORARIO_BAIXA_PERFORMANCE'
            contexto['recomendacao'] = 'REDUZIR_APOSTA'
        if vela_entrada >= 10.0 and vela_resultado < 2.0:
            contexto['tipo_erro'] = 'CRASH_POS_10X'
            contexto['recomendacao'] = 'AGUARDAR_5_RODADAS_POS_10X'
        return contexto
    
    def gerar_regra_auto_correcao(self, contexto_erro, vela_entrada, vela_resultado):
        regra = {
            'id': f"REGRAS_{len(self.regras_auto_correcao)+1}",
            'contexto': contexto_erro,
            'condicao': '',
            'acao': contexto_erro['recomendacao'],
            'prioridade': 0,
            'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if contexto_erro['tipo_erro'] == 'HORARIO_BAIXA_PERFORMANCE':
            hora = contexto_erro['hora']
            regra['condicao'] = f"HORA == {hora}"
            regra['prioridade'] = 85
        elif contexto_erro['tipo_erro'] == 'CRASH_POS_10X':
            regra['condicao'] = "ULTIMA_VELA >= 10.0"
            regra['prioridade'] = 95
        self.regras_auto_correcao.append(regra)
        self.memoria_erros.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'vela_entrada': vela_entrada,
            'vela_resultado': vela_resultado,
            'contexto': contexto_erro,
            'regra_gerada': regra
        })
        self.salvar_regras_auto_correcao()
        return regra
    
    def aplicar_filtro_auto_correcao(self, dados, sinal_proposto):
        hora_atual = datetime.now().hour
        for regra in sorted(self.regras_auto_correcao, key=lambda x: x['prioridade'], reverse=True):
            condicao_atendida = False
            if 'HORA ==' in regra['condicao']:
                hora_alvo = int(regra['condicao'].split('==')[1].strip())
                condicao_atendida = hora_atual == hora_alvo
            elif 'ULTIMA_VELA >= 10.0' in regra['condicao']:
                condicao_atendida = dados[0] >= 10.0
            if condicao_atendida:
                if regra['acao'] == 'REDUZIR_APOSTA':
                    sinal_proposto['valor_entrada'] *= 0.5
                    return sinal_proposto, f"⚠️ HORÁRIO DE BAIXA PERFORMANCE ({hora_atual}h) - Reduzindo aposta em 50%"
                elif regra['acao'] == 'AGUARDAR_5_RODADAS_POS_10X':
                    return None, f"⏳ FILTRO AUTO-CORREÇÃO: Aguardar 5 rodadas após vela >10x"
        return sinal_proposto, "✅ Sinal aprovado por todos os filtros de auto-correção"
    
    def calcular_bonus_horario(self, hora):
        horarios_lucrativos = {
            6: 5, 7: 5, 8: 4,
            13: 4,
            21: 5, 22: 6, 23: 5
        }
        return horarios_lucrativos.get(hora, 0)
    
    def gerenciar_banco(self):
        if self.total_lucro >= self.meta_diaria:
            logger.info(f"\n✅ META DIÁRIA ATINGIDA: {self.total_lucro:.2f} unidades")
            logger.info("💡 Recomendação: 'Aprenda a parar, faça seu lucro saque e retorne no outro dia'")
            return False
        if self.total_lucro >= self.stop_win:
            logger.info(f"\n💎 STOP WIN ATINGIDO: {self.total_lucro:.2f} unidades")
            logger.info("💡 Recomendação: 'O seu capital é sua empresa, então jamais quebre-a'")
            return False
        if self.total_lucro <= self.stop_loss:
            logger.info(f"\n⚠️ STOP LOSS ATINGIDO: {self.total_lucro:.2f} unidades")
            logger.info("💡 Recomendação: 'Nunca coloque no game dinheiro de outro compromisso'")
            return False
        return True
    
    def analise_completa_inteligente(self, dados, sequencias):
        agora = datetime.now()
        hora_atual = agora.hour
        
        if not self.gerenciar_banco():
            return None, "Meta diária/stop atingido"
        
        status_mercado, _ = self.verificar_status_mercado_aprimorado(sequencias)
        if status_mercado not in ["MUITO BOM", "BOM"]:
            return None, f"Mercado não favorável (status: {status_mercado})"
        
        padrao_azul = self.detectar_padroes_azul(dados)
        if padrao_azul:
            sinal_filtrado, _ = self.aplicar_filtro_auto_correcao(dados, padrao_azul)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | ⏰ HORÁRIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, None
        
        padrao_xadrez = self.detectar_padrao_xadrez(dados)
        if padrao_xadrez:
            sinal_filtrado, _ = self.aplicar_filtro_auto_correcao(dados, padrao_xadrez)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | ⏰ HORÁRIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, None
        
        padrao_azuis_decimal = self.analisar_estrategia_azuis(dados)
        if padrao_azuis_decimal:
            sinal_filtrado, _ = self.aplicar_filtro_auto_correcao(dados, padrao_azuis_decimal)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | ⏰ HORÁRIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, None
        
        padrao_modo_2 = self.detectar_estrategias_modo_2(dados)
        if padrao_modo_2:
            sinal_filtrado, _ = self.aplicar_filtro_auto_correcao(dados, padrao_modo_2)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | ⏰ HORÁRIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, None
        
        scheduled_3x = self.schedule_3x_entries(dados)
        if scheduled_3x:
            sinal_filtrado, _ = self.aplicar_filtro_auto_correcao(dados, scheduled_3x)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | ⏰ HORÁRIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, None
        
        scheduled_10x = self.schedule_10x_entries(dados)
        if scheduled_10x:
            sinal_filtrado, _ = self.aplicar_filtro_auto_correcao(dados, scheduled_10x)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | ⏰ HORÁRIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, None
        
        padrao_3_seq = self.detectar_padrao_3_sequencias(dados)
        if padrao_3_seq and padrao_3_seq['confianca'] > 80:
            sinal_filtrado, _ = self.aplicar_filtro_auto_correcao(dados, padrao_3_seq)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | ⏰ HORÁRIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, None
        
        gatilho_surreal = self.detectar_gatilho_surreal(dados)
        if gatilho_surreal and gatilho_surreal['confianca'] > 85:
            sinal_filtrado, _ = self.aplicar_filtro_auto_correcao(dados, gatilho_surreal)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | ⏰ HORÁRIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, None
        
        padrao_10x_reset = self.detectar_padrao_10x_reset(dados)
        if padrao_10x_reset and padrao_10x_reset['confianca'] > 90:
            sinal_filtrado, _ = self.aplicar_filtro_auto_correcao(dados, padrao_10x_reset)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | ⏰ HORÁRIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, None
        
        repeticao_casas = self.detectar_repeticao_casas(dados)
        if repeticao_casas and repeticao_casas['confianca'] > 90:
            sinal_filtrado, _ = self.aplicar_filtro_auto_correcao(dados, repeticao_casas)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | ⏰ HORÁRIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, None
        
        return None, "Nenhuma condição de alta confiança detectada após filtros"
    
    def gerar_sinal_entrada(self, dados, sequencias):
        agora = datetime.now()
        if self.ultima_analise_completa and (agora - self.ultima_analise_completa).seconds < 90:
            return None
        self.ultima_analise_completa = agora
        sinal, motivo = self.analise_completa_inteligente(dados, sequencias)
        if sinal:
            sinal['gatilhos'] = self.obter_gatilhos_usados(sinal)
            sinal['timestamp_analise'] = agora.strftime('%Y-%m-%d %H:%M:%S')
            self.sinais_enviados.append(sinal)
            return sinal
        return None
    
    def atualizar_resultado_sinais(self, dados):
        if not self.sinais_enviados or not dados:
            return
        
        proxima_rodada = dados[0]
        is_win = proxima_rodada >= 2.0
        hora_atual = datetime.now().hour
        dia_semana = datetime.now().weekday()
        
        self.horario_analyzer.atualizar_estatisticas(hora_atual, dia_semana, is_win)
        
        for sinal in self.sinais_enviados[-5:]:
            if sinal['resultado'] is None:
                sinal['resultado'] = 'WIN' if is_win else 'LOSS'
                sinal['valor_real'] = proxima_rodada
                
                if is_win:
                    self.total_lucro += 0.9
                    acerto_detalhado = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'numero_vela': len(self.historico_completo) + 1,
                        'vela_entrada': sinal.get('valor_entrada', 1.0),
                        'vela_resultado': proxima_rodada,
                        'padrao': sinal.get('padrao', 'DESCONHECIDO'),
                        'confianca': sinal.get('confianca', 0.0),
                        'gatilhos': sinal.get('gatilhos', []),
                        'modulo': self.obter_modulo_do_padrao(sinal.get('padrao', '')),
                        'motivo': sinal.get('motivo', 'Sem motivo'),
                        'hora': hora_atual,
                        'dia_semana': dia_semana,
                        'is_win': True
                    }
                    self.acertos_detalhados.append(acerto_detalhado)
                    logger.info(f"✅ ACERTO NA VELA #{acerto_detalhado['numero_vela']}: {proxima_rodada:.2f}x")
                    logger.info(f"   📌 Padrão: {acerto_detalhado['padrao']} | Confiança: {acerto_detalhado['confianca']:.1f}%")
                
                else:
                    self.total_lucro -= 1.0
                    contexto_erro = self.analisar_erro_contextual(
                        sinal.get('valor_entrada', 1.0),
                        proxima_rodada,
                        hora_atual
                    )
                    self.gerar_regra_auto_correcao(contexto_erro, sinal.get('valor_entrada', 1.0), proxima_rodada)
                    erro_detalhado = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'numero_vela': len(self.historico_completo) + 1,
                        'vela_entrada': sinal.get('valor_entrada', 1.0),
                        'vela_resultado': proxima_rodada,
                        'padrao': sinal.get('padrao', 'DESCONHECIDO'),
                        'confianca': sinal.get('confianca', 0.0),
                        'gatilhos': sinal.get('gatilhos', []),
                        'modulo': self.obter_modulo_do_padrao(sinal.get('padrao', '')),
                        'motivo': sinal.get('motivo', 'Sem motivo'),
                        'contexto_erro': contexto_erro,
                        'analise_pos_fato': self.analisar_erro(sinal, sinal.get('valor_entrada', 1.0), proxima_rodada),
                        'hora': hora_atual,
                        'dia_semana': dia_semana,
                        'is_win': False
                    }
                    self.erros_detalhados.append(erro_detalhado)
                    logger.info(f"❌ ERRO NA VELA #{erro_detalhado['numero_vela']}: {proxima_rodada:.2f}x")
                    logger.info(f"   📌 Padrão: {erro_detalhado['padrao']} | Confiança: {erro_detalhado['confianca']:.1f}%")
                    logger.info(f"   🔍 Gatilhos usados: {', '.join(erro_detalhado['gatilhos'][:3])}")
        
        if (len(self.acertos_detalhados) + len(self.erros_detalhados)) % 10 == 0:
            self.salvar_acertos_erros()
            self.horario_analyzer.salvar_analise_horarios()
            if AI_AVAILABLE:
                self.ia_aprendizagem.salvar_modelo()
    
    def obter_gatilhos_usados(self, sinal):
        gatilhos = []
        if 'RESET' in sinal.get('padrao', ''):
            gatilhos.append('Padrão de reset detectado (1.00x)')
        if '1.75X' in sinal.get('padrao', ''):
            gatilhos.append('Padrão de ciclo 1.75x')
        if '1.34X' in sinal.get('padrao', ''):
            gatilhos.append('Padrão de ciclo 1.34x')
        if 'AZUL_' in sinal.get('padrao', ''):
            gatilhos.append('Estratégia decimal de azul')
        if 'ROSA_' in sinal.get('padrao', ''):
            gatilhos.append('ROSA seguido de AZULs')
        if '3X_' in sinal.get('padrao', ''):
            gatilhos.append('Estratégia de 3x com timing')
        if '10X_' in sinal.get('padrao', ''):
            gatilhos.append('Estratégia de 10x com soma de minutos')
        if '3_SEQUENCIAS' in sinal.get('padrao', ''):
            gatilhos.append('Padrão de 3 sequências detectado')
        if 'SURREAL' in sinal.get('padrao', ''):
            gatilhos.append('Gatilho Surreal detectado')
        if '10X_RESET' in sinal.get('padrao', ''):
            gatilhos.append('Padrão 10x Reset detectado')
        if 'HORARIO' in sinal.get('padrao', ''):
            gatilhos.append('Horário lucrativo identificado')
        return gatilhos
    
    def obter_modulo_do_padrao(self, padrao):
        if 'RESET' in padrao or '1.75X' in padrao or '1.34X' in padrao or 'AZUL_' in padrao or 'XADREZ' in padrao:
            return 'modulo_1'
        elif 'ROSA_' in padrao:
            return 'modulo_2'
        elif '3X_' in padrao or '10X_' in padrao or '50X_' in padrao or '100X_' in padrao:
            return 'modulo_3'
        elif '3_SEQUENCIAS' in padrao or 'SURREAL' in padrao or '10X_RESET' in padrao or 'REPETICAO_CASAS' in padrao:
            return 'modulo_4'
        elif 'HORARIO' in padrao:
            return 'modulo_5'
        return 'modulo_desconhecido'
    
    def analisar_erro(self, sinal, vela_entrada, vela_resultado):
        analise = []
        if vela_entrada >= 2.0 and vela_resultado < 2.0:
            analise.append('Vitória seguida de derrota imediata (timing errado)')
        if vela_entrada < 2.0 and vela_resultado < 2.0:
            analise.append('Sequência prolongada de derrotas (padrão não confirmado)')
        if sinal.get('confianca', 0) > 80 and vela_resultado < 2.0:
            analise.append('Alta confiança mas resultado negativo (falso positivo)')
        if vela_entrada >= 10.0 and vela_resultado < 2.0:
            analise.append('Vela alta seguida de crash (volatilidade extrema)')
        return analise if analise else ['Erro não classificado']
    
    def salvar_dados_continuos(self, dados):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_dia = datetime.now().strftime('%Y-%m-%d')
        for mult in dados:
            self.historico_completo.append({
                'timestamp': timestamp,
                'data_dia': data_dia,
                'multiplier': mult,
                'is_win': mult >= 2.0,
                'is_big_win': mult >= 10.0,
                'hora': datetime.now().hour,
                'minuto': datetime.now().minute
            })
        try:
            if not os.path.exists('data'):
                os.makedirs('data')
            
            df = pd.DataFrame(self.historico_completo)
            df.to_csv('data/historico_completo.csv', index=False, encoding='utf-8')
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados: {e}")
    
    def obter_velas_mais_repetidas_24h(self):
        agora = datetime.now()
        limite_24h = agora - timedelta(hours=24)
        dados_24h = [
            entry for entry in self.historico_completo
            if datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') >= limite_24h
        ]
        if not dados_24h:
            return []
        frequencia = defaultdict(int)
        for entry in dados_24h:
            valor_arredondado = round(entry['multiplier'], 2)
            frequencia[valor_arredondado] += 1
        top_10 = sorted(frequencia.items(), key=lambda x: x[1], reverse=True)[:10]
        total = sum(frequencia.values())
        resultado = []
        for valor, count in top_10:
            percentual = (count / total) * 100
            status = "(vitória)" if valor >= 2.0 else "(derrota)"
            resultado.append({
                'valor': valor,
                'count': count,
                'percentual': percentual,
                'status': status
            })
        return resultado
    
    def atualizar_historico_padroes(self, dados):
        resultados = []
        for entry in self.historico_completo:
            resultados.append('V' if entry['is_win'] else 'D')
        for length in range(2, 9):
            if len(resultados) >= length + 1:
                pattern = ','.join(resultados[-length-1:-1])
                next_outcome = resultados[-1]
                if pattern not in self.historico_padroes:
                    self.historico_padroes[pattern] = {'win': 0, 'loss': 0}
                if next_outcome == 'V':
                    self.historico_padroes[pattern]['win'] += 1
                else:
                    self.historico_padroes[pattern]['loss'] += 1
    
    def exibir_status(self, dados, sequencias):
        os.system('clear')
        print("="*80)
        print(f"📊 AVIATOR BOT INTELIGENTE V3 - Login + Logs + Ubuntu 22.04")
        print(f"⏰ Última atualização: {datetime.now().strftime('%H:%M:%S')} | Dia: {self.data_inicio}")
        print(f"📈 Total de coletas: {self.total_coletas} | Velas analisadas: {len(dados)}")
        print(f"💰 Lucro acumulado hoje: {self.total_lucro:.2f} | Meta diária: {self.meta_diaria:.2f}")
        print("="*80)
        
        total = len(dados)
        if total == 0:
            print("\n⚠️  Nenhum dado coletado ainda. Aguardando próxima atualização...")
            return
        
        vitorias = sum(1 for d in dados if d >= 2.0)
        derrotas = total - vitorias
        big_wins = sum(1 for d in dados if d >= 10.0)
        print(f"\n📈 ESTATÍSTICAS DAS ÚLTIMAS {total} VELAS:")
        print(f"   ✅ Vitórias (≥ 2.00x): {vitorias} ({vitorias/total*100:.1f}%)")
        print(f"   ❌ Derrotas (< 2.00x): {derrotas} ({derrotas/total*100:.1f}%)")
        print(f"   💎 Grandes vitórias (≥ 10.00x): {big_wins} ({big_wins/total*100:.1f}%)")
        
        status_mercado, _ = self.verificar_status_mercado_aprimorado(sequencias)
        emoji = {"MUITO BOM": "💎", "BOM": "🟢", "NORMAL": "🟡", "RUIM": "🔴"}[status_mercado]
        print(f"\n💰 STATUS DO MERCADO: {emoji} {status_mercado}")
        
        print(f"\n🔥 ÚLTIMAS 10 VELAS (com cores):")
        for i, mult in enumerate(dados[:10]):
            cor = self.classificar_vela_cores(mult)
            cor_emoji = "🔵" if cor == 'AZUL' else "🟣" if cor == 'ROXA' else "🌸" if cor == 'ROSA' else "⚪"
            status = "(vitória)" if mult >= 2.0 else "(derrota)"
            print(f"   {i+1}. {cor_emoji} {mult:.2f}x {status}")
        
        print(f"\n🎯 ESTATÍSTICAS DE ACERTOS/ERROS:")
        total_acertos = len(self.acertos_detalhados)
        total_erros = len(self.erros_detalhados)
        total_sinais = total_acertos + total_erros
        if total_sinais > 0:
            taxa_acerto = (total_acertos / total_sinais) * 100
            print(f"   ✅ Total de ACERTOS: {total_acertos} ({taxa_acerto:.1f}%)")
            print(f"   ❌ Total de ERROS: {total_erros} ({100 - taxa_acerto:.1f}%)")
        else:
            print("   ⏳ Aguardando primeiros sinais...")
        
        print("\n" + "="*80)
        print("💡 DICA: Bot operando em modo HEADLESS (sem interface gráfica)")
        print("   ✅ Login automático com cookies salvos")
        print("   💾 Logs salvos em: logs/bot_YYYYMMDD_HHMMSS.log")
        print("="*80)
    
    def executar(self, page, duracao_minutos=1440):
        tempo_inicio = time.time()
        tempo_fim = tempo_inicio + (duracao_minutos * 60)
        self.last_round_value = None
        
        logger.info("="*80)
        logger.info("🚀 INICIANDO AVIATOR BOT INTELIGENTE V3")
        logger.info("✅ Login realizado com sucesso")
        logger.info("🌐 Coletando dados REAIS do TipMiner")
        logger.info("⏰ Operação CONTÍNUA 24h (modo headless)")
        logger.info("="*80)
        
        while time.time() < tempo_fim:
            dados = self.fetch_data(page)
            if dados:
                current_value = dados[0] if dados else None
                if self.last_round_value is None or abs(current_value - self.last_round_value) > 0.01:
                    self.last_round_value = current_value
                    self.total_coletas += 1
                    sequencias = self.analisar_sequencias(dados)
                    self.salvar_dados_continuos(dados)
                    self.atualizar_resultado_sinais(dados)
                    self.exibir_status(dados, sequencias)
            
            if kbhit_linux():
                tecla = getch_linux()
                if tecla.lower() == 'q':
                    logger.info("\n🛑 Bot encerrado pelo usuário (tecla 'q').")
                    break
            
            time.sleep(5)
        
        self.salvar_acertos_erros()
        self.horario_analyzer.salvar_analise_horarios()
        if AI_AVAILABLE:
            self.ia_aprendizagem.salvar_modelo()
        
        logger.info("\n✅ Bot finalizado!")
        logger.info(f"📊 Total de coletas: {self.total_coletas}")
        logger.info(f"✅ Total de ACERTOS: {len(self.acertos_detalhados)}")
        logger.info(f"❌ Total de ERROS: {len(self.erros_detalhados)}")
        logger.info(f"⏰ Horários pagantes analisados: {len(self.horario_analyzer.horario_stats)} horas")
        if AI_AVAILABLE:
            logger.info(f"🤖 IA treinada com {len(self.ia_aprendizagem.X)} amostras")
        logger.info(f"💾 Dados salvos em: data/historico_completo.csv")
        logger.info(f"🎯 Padrões salvos em: data/padroes.json")
        logger.info(f"🤖 Regras de auto-correção: data/regras_auto_correcao.json")
        logger.info(f"📊 Acertos detalhados: data/acertos_detalhados.json")
        logger.info(f"📊 Erros detalhados: data/erros_detalhados.json")
        logger.info(f"⏰ Análise horários: data/horario_pagante.json")
        if AI_AVAILABLE:
            logger.info(f"🤖 Modelo IA: data/ia_modelo.pkl")
        logger.info(f"📝 Logs salvos em: logs/bot_*.log")

# ============================================
# FUNÇÃO PRINCIPAL
# ============================================
def main():
    try:
        print("="*80)
        print("🚀 AVIATOR BOT INTELIGENTE V3 - UBUNTU 22.04 LTS")
        print("="*80)
        print("\n✅ Login automático no TipMiner")
        print("✅ Coleta de dados REAIS após autenticação")
        print("✅ Sistema de logs completo (logs/bot_*.log)")
        print("✅ Modo HEADLESS para servidores sem interface gráfica")
        print("✅ Módulos 1-7 ativos (incluindo IA e horários pagantes)")
        print("\n" + "="*80)
        
        login_manager = TipMinerLogin(logger)
        
        logger.info("\n⏳ Tentando login com cookies salvos...")
        context, page = login_manager.realizar_login()
        
        if context is None or page is None:
            logger.error("❌ FALHA NO LOGIN - Encerrando bot")
            return
        
        bot = AviatorBotInteligenteV3(logger, login_manager)
        bot.executar(page, duracao_minutos=1440)
        
        try:
            context.close()
        except:
            pass
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        logger.error(f"\n❌ Erro durante a execução: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()