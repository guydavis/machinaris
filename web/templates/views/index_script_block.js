const COLORS = [
  '#3aac59',
  // https://www.chartjs.org/docs/master/samples/utils.html
  //'#4dc9f6',
  '#f67019',
  '#f53794',
  //'#537bc4',
  '#acc236',
  //'#166a8f',
  //'#00a950',
  //'#58595b',
  '#8549ba',
  // https://colorbrewer2.org/#type=qualitative&scheme=Paired&n=9
  '#a6cee3',
  '#1f78b4',
  '#b2df8a',
  '#33a02c',
  '#fb9a99',
  '#e31a1c',
  '#fdbf6f',
  '#ff7f00',
  '#cab2d6',
  // https://learnui.design/tools/data-color-picker.html#palette
  '#003f5c',
  '#2f4b7c',
  '#665191',
  '#a05195',
  '#d45087',
  '#f95d6a',
  '#ff7c43',
  '#ffa600',
];

function color(index) {
  return COLORS[index % COLORS.length];
}

$(document).ready(function () {
$('[data-toggle="tooltip"]').tooltip();

{% for blockchain in farms %}

{% if farms[blockchain].wallets.dates|length > 0 %}
var ctx = document.getElementById('{{blockchain}}_wallets_chart');
var myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: {{ farms[blockchain].wallets.dates | safe }},
        datasets: [
            {
                label: "{{_('Farmed Coins')}}",
                data: {{ farms[blockchain].wallets.coins | safe }},
                backgroundColor: color(0),
            },
            {
              label: "{{_('Total Balance')}}",
              data: {{ farms[blockchain].wallets.balances | safe }},
              backgroundColor: color(1),
            },
        ],
    },
    borderWidth: 1,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {  
        legend: {
            labels: {
            color: "#c7c7c7",  
            font: {
              size: 18 
            }
          }
        }
      },
      scales: {
          x: {
              type: 'time',
              time: {
                  tooltipFormat: 'DD T'
              },
              ticks: {
                  color: "#c7c7c7",
                  font: {
                    size: 16 
                  }  
              },
              title: {
                  display: true,
                  text: "{{_('Date')}}",
                  color: "#c7c7c7",  
                  font: {
                    size: 18 
                  }
              }
          },
          y: {
              ticks: {
                  color: "#c7c7c7",  
                  font: {
                    size: 16 
                  }
              },
              beginAtZero: true,
              title: {
                  display: true,
                  text: "{{_('Coins')}}",
                  color: "#c7c7c7",  
                  font: {
                    size: 18 
                  }
              }
          }
      }
    }
  });
  {% endif %}

{% if farms[blockchain].challenges.labels|length > 0 %}
var ctx = document.getElementById('{{blockchain}}_challenges_chart');
var myChart = new Chart(ctx, {
    type: 'scatter',
    data: {
        labels: {{ farms[blockchain].challenges.labels | safe }},
        datasets: [
        {% for key in farms[blockchain].challenges.data | sort %}
            {
                label: "{{key}}",
                data: {{ farms[blockchain].challenges.data[key] | safe }},
                backgroundColor: color({{ loop.index - 1 }}),
            },
        {% endfor %}
        ],
    },
    borderWidth: 1,
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {  
          legend: {
              labels: {
              color: "#c7c7c7",  
              font: {
                size: 18 
              }
            }
          }
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    tooltipFormat: 'DD T'
                },
                ticks: {
                    color: "#c7c7c7",
                    font: {
                      size: 16 
                    }  
                },
                title: {
                    display: true,
                    text: "{{_('Time - Recent')}}",
                    color: "#c7c7c7",  
                    font: {
                      size: 18 
                    }
                }
            },
            y: {
                ticks: {
                    color: "#c7c7c7",  
                    font: {
                      size: 16 
                    },
                    beginAtZero: true
                },
                title: {
                    display: true,
                    text: "{{_('Time Taken (seconds)')}}",
                    color: "#c7c7c7",  
                    font: {
                      size: 18 
                    }
                }
            }
        }
    }
  });
{% endif %}

{% if farms[blockchain].partials.data|length > 0 %}
var ctx = document.getElementById('{{blockchain}}_partials_chart');
var myChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: {{ farms[blockchain].partials.labels | safe }},
        datasets: [
        {% for key in farms[blockchain].partials.data %}
            {
                label: "{{key}}",
                data: {{ farms[blockchain].partials.data[key] | safe }},
                backgroundColor: color({{ loop.index - 1 }}),
            },
        {% endfor %}
        ],
    },
    borderWidth: 1,
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {  
          legend: {
              labels: {
              color: "#c7c7c7",  
              font: {
                size: 18 
              }
            }
          }
        },
        scales: {
            x: {
                ticks: {
                    color: "#c7c7c7",
                    font: {
                      size: 16 
                    }  
                },
                title: {
                    display: true,
                    text: "{{_('Time - Last 24 Hours')}}",
                    color: "#c7c7c7",  
                    font: {
                      size: 18 
                    }
                }
            },
            y: {
                ticks: {
                    color: "#c7c7c7",
                    font: {
                      size: 16 
                    }  
                },
                beginAtZero: true,
                title: {
                    display: true,
                    text: "{{_('Partials Submitted')}}",
                    color: "#c7c7c7",  
                    font: {
                      size: 18 
                    }
                }
            }
        }
    }
  });
  {% endif %}
  {% endfor %}
})