from pathlib import Path
from playwright.sync_api import sync_playwright
import json
root=Path(__file__).resolve().parents[1]
html=(root/'runtime/index.html').read_text()
config={
'delay_ms':120,'smooth_pct':26,'deadband':0,'flash_guard_frames':2,'flash_guard_delta':100,
'brightness':18,'top_pct':4,'right_pct':3,'bottom_pct':1,'left_pct':3,'red_pct':90,
'green_pct':115,'blue_pct':100,'saturation_pct':175,'gamma_red':180,'gamma_green':180,'gamma_blue':180}
status={'running':1,'fps':24.85,'ms':21.74,'sent':48552,'changed':48020,'over40':6,'guard_held':17,'guard_confirmed':26,'cpu_pct':38,'ram_pct':42,'ram_used_mb':108,'ram_total_mb':256}
layout={'top':100,'right':57,'bottom':100,'left':57,'start':'TL','direction':'CW','offset':0,'total':314,'max_leds':480}
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1366,'height':850},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    async_js="""(data) => {window.fetch = async (path,options) => ({ ok:true, json:async()=> path.startsWith('/api/config') ? data.config : path.startsWith('/api/led/layout') ? data.layout : data.status });}"""
    def load():
        page.goto('about:blank')
        page.evaluate(async_js,{'config':config,'layout':layout,'status':status})
        page.set_content(html,wait_until='load')
    load()
    page.wait_for_timeout(1150)
    assert page.locator('#sys-cpu').inner_text()=='38 %'
    assert page.locator('#sys-ram').inner_text()=='42 %'
    assert page.locator('#sys-ram-detail').inner_text()=='108 / 256 MB'
    assert page.locator('#s-running').inner_text()=='AKTIV'
    assert page.locator('#sys-cpu-bar').evaluate('(e)=>e.style.width')=='38%'
    assert not errors,errors
    page.screenshot(path=str(root/'preview_cpu_ram_desktop.png'),full_page=False)
    page.get_by_role('button',name='LED-Anordnung').first.click()
    assert page.locator('#openLedDialog').is_visible()
    page.locator('#openLedDialog').click()
    assert page.locator('#ledDialog').evaluate('(e)=>e.open')
    page.locator('#closeLedDialog').click()
    page.set_viewport_size({'width':390,'height':844})
    load()
    page.wait_for_timeout(250)
    assert page.locator('#sys-cpu').is_visible()
    assert page.locator('#sys-ram').is_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile horizontal scrolling'
    page.screenshot(path=str(root/'preview_cpu_ram_mobile.png'),full_page=False)
    assert not errors,errors
    browser.close()
print('PASS: desktop and mobile, auto-updating values, tab navigation, LED dialog, no JS errors')
