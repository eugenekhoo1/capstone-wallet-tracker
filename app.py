from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
import pnl
import tokenflows

app = Flask(__name__)
app.secret_key = 'password'
app.permanent_session_lifetime = timedelta(minutes=10) # session data stored for n minutes; store data in sessions

@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        session.permanent = True # session defined as permanent session; default is false - lose session data after browser closes
        user = request.form['nm'] # text stored in form as name variable
        session['user'] = user # store text as value in session dictionary
        return redirect(url_for('dashboard'))
    else:
        if 'user' in session: # retrieving session data
            return redirect(url_for('dashboard')) 
        else:
            return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        user = session['user']
        flash(f"You have been logged out, {user}", 'info') # show message after logging out
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        user = session['user']
    else:
        return redirect(url_for('login'))
    pnl_dict = pnl.cross_sec_pnl(user, 'uniswapv2_1') # uniswapv2_1 to be looped for different protocols in future
    #last_10_trades_dict = pnl_dict['last_10_trades']
    template_dict = {
        'last_10_trades' : pnl_dict['last_10_trades'],
        'transaction_count' : pnl_dict['transaction_count'], 
        'total_volume' : pnl_dict['total_volume'], 
        'realized_profit' : pnl_dict['realized_profit'], 
        'unrealized_profit' : pnl_dict['unrealized_profit'],
        'pnl' : pnl_dict['pnl'],
        'user' : user
    }

    return render_template('dashboard.html', **template_dict)

@app.route('/flows')
def flows():
    if 'user' in session:
        user = session['user']
    else:
        return redirect(url_for('login'))
    
    # USDC Flows
    tokenflow_dict = tokenflows.get_one_hop(user)

    return render_template('flows.html', tokenflow_dict=tokenflow_dict)

if __name__ == '__main__':
    app.run(debug=True)
 
    