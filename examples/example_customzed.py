
# A super basic microdot web-server.
# To include your own content, and leverage this libraries assets and templates.
# This doesn't run as is, this is here to show how to just use the assets as is.

import uasyncio as asyncio
from microdot.microdot import Microdot, Response  # type: ignore [import-untyped]
from microdot.utemplate import Template   # type: ignore [import-untyped]
from utemplate import source, recompile, compiled
import uwifisetup.util as util
import uwifisetup.log as log

async def start():
    app = Microdot()
    Response.default_content_type = 'text/html'
    Template.initialize(template_dir=const.WWW_FILE_ROOT, loader_class=source.Loader)

    @app.route('/')
    async def getRoot(request):
        return Response.redirect('/index.html')


    @app.route('/index.html', methods=['GET','POST'])
    async def getIndex(request):
        message = "foo"

        return Template("index.html").generate_async(
            message=message
        )

    @app.route('/_uwifisetup/assets/<asset>')
    async def getAssets(request, asset):
        return await getStatic(request=request, asset=asset)


    @app.route('/assets/<asset>')
    async def getStatic(request, asset):
        """
        Static content
        """
        if '..' in asset:
            # directory traversal is not allowed
            return 'Not found', 404

        file = f"{const.WWW_FILE_ROOT}{request.path}"
        contType = "text/plain"
        if file.endswith(".css"):
            contType = "text/css"
        if file.endswith(".ico"):
            contType = "image/vnd.microsoft.icon"
        if file.endswith(".jpg"):
            contType = "image/jpeg"
        if file.endswith(".png"):
            contType = "image/png"
        if file.endswith(".svg"):
            contType = "image/svg+xml"

        compressed = False
        gzfile = f"{file}.gz"

        if util.file_exists(gzfile):
            file = gzfile
            compressed = True

        if not util.file_exists(file):
            log.warn(__name__, f"File Not Found [{file}] -> 404")
            return "Not Found", 404

        return Response.send_file(file, content_type=contType, compressed=compressed, max_age=3600)


    # Lastly, start up the server
    await app.start_server(port=80, debug=True)


asyncio.get_event_loop().run_until_complete( start() )